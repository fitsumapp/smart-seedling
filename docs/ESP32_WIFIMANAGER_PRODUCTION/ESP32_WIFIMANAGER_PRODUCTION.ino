/*
 * ==============================================================================
 * 🌱 Smart Seedling Nursery IoT - Production ESP32 Firmware with Relay Support
 * ==============================================================================
 * Note on Relays:
 *   Most standard 5V Relay Modules are ACTIVE-LOW (LOW = ON, HIGH = OFF).
 *   Set RELAY_ACTIVE_LOW = true below if your relay turns on with LOW.
 * ==============================================================================
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <WiFiManager.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ==============================================================================
// 1. CLOUD SERVER CONFIGURATION
// ==============================================================================
const char* SERVER_URL    = "https://seedling.acrmatech.com/api/v1/device/readings/";
const char* DEVICE_ID     = "ESP32-001";
const char* API_KEY       = "secret-esp32-demo-api-key-2026";
const char* FIRMWARE_VER  = "1.0.0";

// ==============================================================================
// 2. HARDWARE PINS & RELAY CONFIGURATION
// ==============================================================================
#define PIN_DS18B20       4     // DS18B20 1-Wire Data
#define PIN_MOISTURE      34    // Capacitive Soil Moisture Analog Pin
#define PIN_RELAY         27    // Pump Relay Pin

// ⚠️ RELAY TYPE: Set to TRUE for standard Active-LOW relays (90% of Arduino relays)
// Set to FALSE only if your relay is Active-HIGH.
const bool RELAY_ACTIVE_LOW = true;

// Moisture ADC Calibration
const int DRY_ADC_VALUE   = 3200;  // Value in air
const int WET_ADC_VALUE   = 1350;  // Value in water

// Irrigation Thresholds
float PUMP_ON_THRESHOLD   = 30.0;  // Turn ON when moisture <= 30%
float PUMP_OFF_THRESHOLD  = 50.0;  // Turn OFF when moisture >= 50%
unsigned long MAX_PUMP_RUN_MS = 30000; // 30 seconds max safety run

OneWire oneWire(PIN_DS18B20);
DallasTemperature tempSensors(&oneWire);

unsigned long lastUploadTime = 0;
const unsigned long UPLOAD_INTERVAL_MS = 2000; // Send telemetry every 2s
unsigned long pumpStartTime = 0;
bool isPumpActive = false;

// Helper to set physical relay state correctly
void setPumpHardware(bool turnOn) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(PIN_RELAY, turnOn ? LOW : HIGH);
  } else {
    digitalWrite(PIN_RELAY, turnOn ? HIGH : LOW);
  }
}

// ==============================================================================
// 3. SETUP
// ==============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n🌱 ==================================================");
  Serial.println("🌱 Smart Seedling ESP32 Node Booting...");
  Serial.println("🌱 Target Server: https://seedling.acrmatech.com");
  Serial.println("🌱 ==================================================");

  // 1. Setup Relay Pin and ensure pump is OFF
  pinMode(PIN_RELAY, OUTPUT);
  setPumpHardware(false); // Pump initially OFF

  // Quick relay test click on boot:
  Serial.println("⚡ Testing Relay Click (1 sec ON then OFF)...");
  setPumpHardware(true);
  delay(800);
  setPumpHardware(false);
  Serial.println("⚡ Relay Test Complete.");

  pinMode(PIN_MOISTURE, INPUT);
  tempSensors.begin();

  // 2. Connect Wi-Fi via Phone Portal
  WiFiManager wm;
  wm.autoConnect("SmartSeedling-Setup");
  Serial.println("\n✅ Wi-Fi Connected!");
}

// ==============================================================================
// 4. MAIN LOOP
// ==============================================================================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    delay(100);
    return;
  }

  // 1. Read Temperature
  tempSensors.requestTemperatures();
  float soilTemp = tempSensors.getTempCByIndex(0);
  if (soilTemp == DEVICE_DISCONNECTED_C || soilTemp < -40.0) {
    soilTemp = 24.5;
  }

  // 2. Read Moisture
  int rawMoist = analogRead(PIN_MOISTURE);
  float soilMoist = calculateMoisturePercent(rawMoist);

  // 3. Control Irrigation Pump
  handleIrrigation(soilMoist);

  // 4. Send Telemetry to Server
  unsigned long now = millis();
  if (now - lastUploadTime >= UPLOAD_INTERVAL_MS) {
    lastUploadTime = now;
    sendTelemetry(soilTemp, soilMoist, rawMoist, isPumpActive);
  }

  delay(100);
}

// ==============================================================================
// 5. HELPER FUNCTIONS
// ==============================================================================

float calculateMoisturePercent(int rawADC) {
  if (rawADC >= DRY_ADC_VALUE) return 0.0;
  if (rawADC <= WET_ADC_VALUE) return 100.0;
  float pct = ((float)(DRY_ADC_VALUE - rawADC) / (float)(DRY_ADC_VALUE - WET_ADC_VALUE)) * 100.0;
  return constrain(pct, 0.0, 100.0);
}

void handleIrrigation(float currentMoisture) {
  // If moisture is DRY (<= 30%) and pump is currently OFF -> Turn ON
  if (!isPumpActive && currentMoisture <= PUMP_ON_THRESHOLD) {
    setPumpHardware(true);
    isPumpActive = true;
    pumpStartTime = millis();
    Serial.printf("💧 [PUMP ON] Soil Moisture (%.1f%%) <= Threshold (%.1f%%)\n", currentMoisture, PUMP_ON_THRESHOLD);
  }
  // If pump is ON and moisture reaches WET (>= 50%) or Timeout -> Turn OFF
  else if (isPumpActive) {
    bool moistureSatisfied = (currentMoisture >= PUMP_OFF_THRESHOLD);
    bool timeoutExceeded = (millis() - pumpStartTime >= MAX_PUMP_RUN_MS);

    if (moistureSatisfied || timeoutExceeded) {
      setPumpHardware(false);
      isPumpActive = false;
      if (timeoutExceeded) {
        Serial.println("⚠️ [PUMP OFF] 30-second safety cutoff reached.");
      } else {
        Serial.printf("✅ [PUMP OFF] Target Moisture reached (%.1f%% >= %.1f%%)\n", currentMoisture, PUMP_OFF_THRESHOLD);
      }
    }
  }
}

void sendTelemetry(float temp, float moist, int rawMoist, bool pumpState) {
  if (WiFi.status() != WL_CONNECTED) return;

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient https;
  https.setTimeout(4000);

  if (https.begin(client, SERVER_URL)) {
    https.addHeader("Content-Type", "application/json");
    https.addHeader("X-Device-ID", DEVICE_ID);
    https.addHeader("X-API-Key", API_KEY);

    StaticJsonDocument<256> doc;
    doc["device_id"]         = DEVICE_ID;
    doc["soil_temperature"]  = temp;
    doc["soil_moisture"]     = moist;
    doc["soil_moisture_raw"] = rawMoist;
    doc["pump_status"]       = pumpState;
    doc["rssi"]              = WiFi.RSSI();
    doc["firmware_version"]  = FIRMWARE_VER;

    String requestBody;
    serializeJson(doc, requestBody);

    int httpCode = https.POST(requestBody);

    if (httpCode == HTTP_CODE_CREATED || httpCode == HTTP_CODE_OK) {
      Serial.printf("📡 [CLOUD SYNC OK] Temp: %.1f°C | Moist: %.1f%% | Pump: %s | RSSI: %d dBm\n",
                    temp, moist, pumpState ? "ON" : "OFF", WiFi.RSSI());
    } else {
      Serial.printf("❌ [CLOUD SYNC ERROR] HTTP %d\n", httpCode);
    }
    https.end();
  }
}
