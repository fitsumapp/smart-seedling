# ESP32 Integration & Hardware Firmware Guide

## Hardware Specifications & Pinout

* **Microcontroller**: ESP32 DevKit V1 (38-pin or 30-pin)
* **Temperature Sensor**: DS18B20 1-Wire Digital Soil/Ambient Temperature Sensor
* **Moisture Sensor**: Capacitive Soil Moisture Sensor v1.2 / v2.0 (Analog output)
* **Actuator Relay**: 5V Active-High / Active-Low Relay Module
* **Pump**: 5V Submersible DC Mini Water Pump

### Wiring Table

| Component Pin | ESP32 GPIO | Notes |
|---|---|---|
| DS18B20 DATA | **GPIO 4** | Requires 4.7kΩ pull-up resistor to 3.3V |
| Capacitive Moisture AOUT | **GPIO 34** | ADC1_CH6 (Input-only, no internal pull-ups) |
| Relay Module IN | **GPIO 27** | Digital output driving transistor/optocoupler |
| DS18B20 / Moisture VCC | 3.3V | Powered from 3.3V rail |
| Relay VCC / Pump Power | 5V (VIN / External) | Powered from isolated 5V power supply |
| Ground | GND | Common ground across all components |

---

## Local Autonomous Logic vs. Cloud Sync

The ESP32 firmware executes a local non-blocking state machine in `loop()`:

1. **Local Control (Resilient Fallback)**:
   * Every `reading_interval_seconds` (default: 2s):
     * Read analog ADC value from GPIO 34 (0 - 4095).
     * Calculate calibrated moisture percentage $M = \frac{ADC_{dry} - ADC_{raw}}{ADC_{dry} - ADC_{wet}} \times 100\%$.
     * Read temperature from DS18B20 on GPIO 4.
     * If `automatic_mode == true`:
       * If $M \le \text{pump\_on\_threshold}$ (e.g. 30%) $\rightarrow$ Turn relay ON.
       * If $M \ge \text{pump\_off\_threshold}$ (e.g. 50%) $\rightarrow$ Turn relay OFF.
       * If pump has been ON continuously for longer than `max_pump_runtime_seconds` (e.g. 30s) $\rightarrow$ Force relay OFF (Safety cutoff).

2. **Cloud Synchronization (REST Ingestion)**:
   * Every `upload_interval_seconds` (default: 10s):
     * Send HTTP POST to `/api/v1/device/readings/` with current sensor values, pump status, Wi-Fi RSSI, and firmware version.
   * Periodically (e.g. on boot and every 10 minutes):
     * Send HTTP GET to `/api/v1/device/settings/` to update threshold values stored in non-volatile flash (Preferences / NVS).

---

## Example ESP32 C++ (Arduino Framework) Code Snippet

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

#define PIN_DS18B20    4
#define PIN_MOISTURE   34
#define PIN_RELAY      27

const char* SERVER_URL = "http://192.168.1.100:8000/api/v1/device/readings/";
const char* DEVICE_ID  = "ESP32-001";
const char* API_KEY    = "secret-esp32-demo-api-key-2026";
const char* FIRMWARE   = "1.0.0";

OneWire oneWire(PIN_DS18B20);
DallasTemperature tempSensors(&oneWire);

void uploadReading(float temp, float moisture, int rawMoisture, bool pumpState) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-ID", DEVICE_ID);
  http.addHeader("X-API-Key", API_KEY);

  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["soil_temperature"] = temp;
  doc["soil_moisture"] = moisture;
  doc["soil_moisture_raw"] = rawMoisture;
  doc["pump_status"] = pumpState;
  doc["rssi"] = WiFi.RSSI();
  doc["firmware_version"] = FIRMWARE;

  String requestBody;
  serializeJson(doc, requestBody);

  int httpCode = http.POST(requestBody);
  if (httpCode == HTTP_CODE_CREATED || httpCode == HTTP_CODE_OK) {
    Serial.println("Telemetry successfully dispatched to Smart Seedling cloud.");
  } else {
    Serial.printf("HTTP upload failed with status code: %d\n", httpCode);
  }
  http.end();
}
```
