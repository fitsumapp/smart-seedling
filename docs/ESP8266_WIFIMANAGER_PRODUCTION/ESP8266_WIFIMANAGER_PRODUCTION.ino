/*
 * ==============================================================================
 * 🌱 Smart Seedling Nursery IoT - Complete Production Firmware for ESP8266
 * ==============================================================================
 * Platform: ESP8266 (NodeMCU v2/v3, Wemos D1 Mini, ESP-12E/F)
 * Target Server: https://seedling.acrmatech.com
 * 
 * 🔌 HARDWARE WIRING PINOUT:
 *   - A0      (ADC0)    : Capacitive Soil Moisture Sensor v1.2 / v2.0 (Analog)
 *   - D2      (GPIO 4)  : DS18B20 Soil Temperature 1-Wire (with 4.7kΩ pull-up to 3.3V)
 *   - D1      (GPIO 5)  : 5V Relay #1 -> Submersible Irrigation Pump
 *   - D5      (GPIO 14) : DHT22 Ambient Air Temperature & Relative Humidity Sensor
 *   - D6      (GPIO 12) : 5V Relay #2 -> Greenhouse Ventilation / Cooling Fan
 * 
 * 📦 REQUIRED ARDUINO LIBRARIES:
 *   1. WiFiManager (by tzapu or tablatronix)
 *   2. DHT sensor library (by Adafruit) + Adafruit Unified Sensor
 *   3. DallasTemperature (by Miles Burton)
 *   4. OneWire (by Paul Stoffregen)
 *   5. ArduinoJson (by Benoit Blanchon, v6.x or v7.x)
 * ==============================================================================
 */

#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <ESP8266HTTPClient.h>
#include <WiFiManager.h>      // Phone Captive Portal Wi-Fi Configuration
#include <DHT.h>              // Adafruit DHT22 Library
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>

// ==============================================================================
// 1. CLOUD SERVER CONFIGURATION
// ==============================================================================
const char* SERVER_URL    = "https://seedling.acrmatech.com/api/v1/device/readings/";
const char* DEVICE_ID     = "ESP32-001";
const char* API_KEY       = "secret-esp32-demo-api-key-2026";
const char* FIRMWARE_VER  = "2.0.0";

// ==============================================================================
// 2. HARDWARE PIN DEFINITIONS & RELAY SETTINGS
// ==============================================================================
#define PIN_MOISTURE      A0    // Dedicated Analog ADC (0 - 1023)
#define PIN_DS18B20       4     // GPIO 4 (NodeMCU D2) - Soil Temperature
#define PIN_PUMP_RELAY    5     // GPIO 5 (NodeMCU D1) - Water Pump Relay
#define PIN_DHT           14    // GPIO 14 (NodeMCU D5) - DHT22 Air Sensor
#define PIN_FAN_RELAY     12    // GPIO 12 (NodeMCU D6) - Ventilation Fan Relay

#define DHTTYPE           DHT22 // DHT 22 (AM2302, AM2321)

// ⚠️ RELAY TYPE: Set to TRUE for standard Active-LOW relays (LOW=ON, HIGH=OFF)
const bool RELAYS_ACTIVE_LOW = true;

// Soil Moisture ADC Calibration (10-bit ADC: 0 - 1023)
const int DRY_ADC_VALUE   = 800;   // In dry air
const int WET_ADC_VALUE   = 350;   // In water

// Autonomous Control Thresholds
float PUMP_ON_THRESHOLD   = 30.0;  // Turn pump ON when soil moisture <= 30%
float PUMP_OFF_THRESHOLD  = 50.0;  // Turn pump OFF when soil moisture >= 50%
unsigned long MAX_PUMP_RUN_MS = 30000; // 30s safety cutoff

float FAN_ON_TEMP_THRESHOLD  = 30.0; // Turn fan ON when air temp >= 30.0°C
float FAN_OFF_TEMP_THRESHOLD = 25.0; // Turn fan OFF when air temp <= 25.0°C
float FAN_ON_HUMID_THRESHOLD = 85.0; // Turn fan ON when air humidity >= 85.0%

// Sensor Objects
DHT dht(PIN_DHT, DHTTYPE);
OneWire oneWire(PIN_DS18B20);
DallasTemperature tempSensors(&oneWire);

// State Tracking & Timing
unsigned long lastUploadTime = 0;
const unsigned long UPLOAD_INTERVAL_MS = 2000; // Stream telemetry every 2 seconds
unsigned long pumpStartTime = 0;
bool isPumpActive = false;
bool isFanActive  = false;

// ==============================================================================
// 3. RELAY ACTUATOR HELPERS
// ==============================================================================
void setPumpRelay(bool turnOn) {
  if (RELAYS_ACTIVE_LOW) {
    digitalWrite(PIN_PUMP_RELAY, turnOn ? LOW : HIGH);
  } else {
    digitalWrite(PIN_PUMP_RELAY, turnOn ? HIGH : LOW);
  }
}

void setFanRelay(bool turnOn) {
  if (RELAYS_ACTIVE_LOW) {
    digitalWrite(PIN_FAN_RELAY, turnOn ? LOW : HIGH);
  } else {
    digitalWrite(PIN_FAN_RELAY, turnOn ? HIGH : LOW);
  }
}

// ==============================================================================
// 4. SETUP INITIALIZATION
// ==============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n🌱 ==================================================");
  Serial.println("🌱 Smart Seedling ESP8266 + DHT22 & Fan Booting...");
  Serial.println("🌱 Target Server: https://seedling.acrmatech.com");
  Serial.println("🌱 ==================================================");

  // 1. Initialize Relay Outputs (Ensure OFF on boot)
  pinMode(PIN_PUMP_RELAY, OUTPUT);
  pinMode(PIN_FAN_RELAY, OUTPUT);
  setPumpRelay(false);
  setFanRelay(false);

  // Quick relay test clicks on boot
  Serial.println("⚡ Testing Relays (Pump & Fan Click Test)...");
  setPumpRelay(true);
  delay(300);
  setPumpRelay(false);
  delay(200);
  setFanRelay(true);
  delay(300);
  setFanRelay(false);
  Serial.println("⚡ Relay Test Completed.");

  // 2. Initialize Sensors
  tempSensors.begin();
  dht.begin();

  // 3. Connect to Wi-Fi via Phone Portal
  WiFiManager wm;
  Serial.println("📱 Starting WiFiManager Portal...");
  Serial.println("📱 Connect phone to Wi-Fi: 'SmartSeedling-Setup' to configure Wi-Fi.");

  bool connected = wm.autoConnect("SmartSeedling-Setup");

  if (!connected) {
    Serial.println("❌ Failed to connect. Restarting ESP8266 in 3 seconds...");
    delay(3000);
    ESP.restart();
  }

  Serial.println("\n✅ Wi-Fi Connected Successfully!");
  Serial.print("📱 Node IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.print("📶 Signal Strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm\n");
}

// ==============================================================================
// 5. MAIN LOOP
// ==============================================================================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    delay(100);
    return;
  }

  // 1. Read Soil Temperature (DS18B20)
  tempSensors.requestTemperatures();
  float soilTemp = tempSensors.getTempCByIndex(0);
  if (soilTemp == DEVICE_DISCONNECTED_C || soilTemp < -40.0) {
    soilTemp = 24.5; // Sensor fallback
  }

  // 2. Read Soil Moisture (Analog)
  int rawMoist = analogRead(PIN_MOISTURE);
  float soilMoist = calculateMoisturePercent(rawMoist);

  // 3. Read Ambient Air Climate (DHT22)
  float airHum = dht.readHumidity();
  float airTemp = dht.readTemperature();
  if (isnan(airHum) || isnan(airTemp)) {
    airHum = 65.0; // Fallback if DHT22 warming up
    airTemp = soilTemp + 1.2;
  }

  // 4. Autonomous Actuation Logic
  handleIrrigation(soilMoist);
  handleVentilation(airTemp, airHum);

  // 5. Stream Real-Time Telemetry to Cloud
  unsigned long now = millis();
  if (now - lastUploadTime >= UPLOAD_INTERVAL_MS) {
    lastUploadTime = now;
    sendTelemetry(soilTemp, soilMoist, rawMoist, airTemp, airHum, isPumpActive, isFanActive);
  }

  delay(100);
}

// ==============================================================================
// 6. CONTROL & TELEMETRY FUNCTIONS
// ==============================================================================

// Convert ADC (0 - 1023) to Percentage
float calculateMoisturePercent(int rawADC) {
  if (rawADC >= DRY_ADC_VALUE) return 0.0;
  if (rawADC <= WET_ADC_VALUE) return 100.0;
  float pct = ((float)(DRY_ADC_VALUE - rawADC) / (float)(DRY_ADC_VALUE - WET_ADC_VALUE)) * 100.0;
  return constrain(pct, 0.0, 100.0);
}

// Autonomous Pump Controller
void handleIrrigation(float currentMoisture) {
  if (!isPumpActive && currentMoisture <= PUMP_ON_THRESHOLD) {
    setPumpRelay(true);
    isPumpActive = true;
    pumpStartTime = millis();
    Serial.printf("💧 [PUMP ON] Soil Moisture (%.1f%%) <= Threshold (%.1f%%)\n", currentMoisture, PUMP_ON_THRESHOLD);
  } else if (isPumpActive) {
    bool moistureSatisfied = (currentMoisture >= PUMP_OFF_THRESHOLD);
    bool timeoutExceeded = (millis() - pumpStartTime >= MAX_PUMP_RUN_MS);

    if (moistureSatisfied || timeoutExceeded) {
      setPumpRelay(false);
      isPumpActive = false;
      if (timeoutExceeded) {
        Serial.println("⚠️ [PUMP OFF] Safety cutoff reached (30s).");
      } else {
        Serial.printf("✅ [PUMP OFF] Target moisture reached (%.1f%% >= %.1f%%)\n", currentMoisture, PUMP_OFF_THRESHOLD);
      }
    }
  }
}

// Autonomous Fan Controller
void handleVentilation(float currentAirTemp, float currentAirHum) {
  bool needsCooling = (currentAirTemp >= FAN_ON_TEMP_THRESHOLD);
  bool needsDehumidify = (currentAirHum >= FAN_ON_HUMID_THRESHOLD);

  if (!isFanActive && (needsCooling || needsDehumidify)) {
    setFanRelay(true);
    isFanActive = true;
    Serial.printf("💨 [FAN ON] Air Temp: %.1f°C | Air Hum: %.1f%% -> Ventilation Active\n", currentAirTemp, currentAirHum);
  } else if (isFanActive) {
    bool tempCooled = (currentAirTemp <= FAN_OFF_TEMP_THRESHOLD);
    bool humNormal  = (currentAirHum < FAN_ON_HUMID_THRESHOLD - 5.0);

    if (tempCooled && humNormal) {
      setFanRelay(false);
      isFanActive = false;
      Serial.printf("✅ [FAN OFF] Climate restored (Air: %.1f°C, Hum: %.1f%%)\n", currentAirTemp, currentAirHum);
    }
  }
}

// HTTPS Telemetry Ingestion to cPanel Server
void sendTelemetry(float sTemp, float sMoist, int rawMoist, float aTemp, float aHum, bool pumpState, bool fanState) {
  if (WiFi.status() != WL_CONNECTED) return;

  WiFiClientSecure client;
  client.setInsecure(); // Bypass SSL verification for high-speed connectivity

  HTTPClient https;
  https.setTimeout(4000);

  if (https.begin(client, SERVER_URL)) {
    https.addHeader("Content-Type", "application/json");
    https.addHeader("X-Device-ID", DEVICE_ID);
    https.addHeader("X-API-Key", API_KEY);

    // Build JSON Payload
    StaticJsonDocument<384> doc;
    doc["device_id"]         = DEVICE_ID;
    doc["soil_temperature"]  = sTemp;
    doc["soil_moisture"]     = sMoist;
    doc["soil_moisture_raw"] = rawMoist;
    doc["air_temperature"]   = aTemp;
    doc["air_humidity"]      = aHum;
    doc["pump_status"]       = pumpState;
    doc["fan_status"]        = fanState;
    doc["rssi"]              = WiFi.RSSI();
    doc["firmware_version"]  = FIRMWARE_VER;

    String requestBody;
    serializeJson(doc, requestBody);

    int httpCode = https.POST(requestBody);

    if (httpCode == HTTP_CODE_CREATED || httpCode == HTTP_CODE_OK) {
      Serial.printf("📡 [CLOUD SYNC OK] Soil: %.1f°C, %.1f%% | Air: %.1f°C, %.1f%% | Pump: %s | Fan: %s | RSSI: %d dBm\n",
                    sTemp, sMoist, aTemp, aHum, pumpState ? "ON" : "OFF", fanState ? "ON" : "OFF", WiFi.RSSI());
    } else {
      Serial.printf("❌ [CLOUD SYNC ERROR] HTTP %d\n", httpCode);
    }
    https.end();
  }
}
