/*
 * ==============================================================================
 * Smart Seedling Nursery IoT - Production Firmware for ESP32
 * ==============================================================================
 * Target Platform: ESP32 DevKit V1 (30-pin or 38-pin)
 * Target Server:   https://seedling.acrmatech.com
 * Hardware Pins:
 *   - GPIO 4  : DS18B20 1-Wire Digital Temperature Sensor (with 4.7kΩ Pull-Up)
 *   - GPIO 34 : Capacitive Soil Moisture Sensor v1.2 / v2.0 (Analog Input)
 *   - GPIO 27 : 5V Active-High Relay Module (Controls Water Pump)
 * ==============================================================================
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ==============================================================================
// 1. NETWORK & CLOUD SERVER CONFIGURATION
// ==============================================================================
const char* WIFI_SSID     = "Fitsum 6G";            // Your Wi-Fi Name (SSID)
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // Your Wi-Fi Password

const char* SERVER_URL    = "https://seedling.acrmatech.com/api/v1/device/readings/";
const char* DEVICE_ID     = "ESP32-001";
const char* API_KEY       = "secret-esp32-demo-api-key-2026";
const char* FIRMWARE_VER  = "1.0.0";

// ==============================================================================
// 2. HARDWARE PIN DEFINITIONS & CONSTANTS
// ==============================================================================
#define PIN_DS18B20       4     // 1-Wire bus for DS18B20
#define PIN_MOISTURE      34    // ADC1 Channel 6
#define PIN_RELAY         27    // Pump relay control pin

// Soil Moisture ADC Calibration (12-bit ADC: 0 - 4095)
const int DRY_ADC_VALUE   = 3200;  // Value in completely dry air
const int WET_ADC_VALUE   = 1350;  // Value submerged in pure water

// Autonomous Irrigation Thresholds (Local Resilient Fallback)
float PUMP_ON_THRESHOLD   = 30.0;  // Turn ON when moisture <= 30%
float PUMP_OFF_THRESHOLD  = 50.0;  // Turn OFF when moisture >= 50%
unsigned long MAX_PUMP_RUN_MS = 30000; // 30 seconds max pump safety cutoff

// Sensor Objects
OneWire oneWire(PIN_DS18B20);
DallasTemperature tempSensors(&oneWire);

// Timing Variables
unsigned long lastUploadTime = 0;
const unsigned long UPLOAD_INTERVAL_MS = 3000; // Upload reading every 3 seconds
unsigned long pumpStartTime = 0;
bool isPumpActive = false;

// ==============================================================================
// 3. SETUP INITIALIZATION
// ==============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n🌱 =========================================");
  Serial.println("🌱 Smart Seedling ESP32 Node Booting...");
  Serial.println("🌱 Target Server: https://seedling.acrmatech.com");
  Serial.println("🌱 =========================================");

  // Configure Pins
  pinMode(PIN_RELAY, OUTPUT);
  digitalWrite(PIN_RELAY, LOW); // Ensure pump is OFF on boot
  pinMode(PIN_MOISTURE, INPUT);

  // Initialize Temperature Sensor
  tempSensors.begin();

  // Connect to Wi-Fi
  connectWiFi();
}

// ==============================================================================
// 4. MAIN LOOP (NON-BLOCKING STATE MACHINE)
// ==============================================================================
void loop() {
  // Ensure Wi-Fi stays connected
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // 1. Read Sensors
  tempSensors.requestTemperatures();
  float soilTemp = tempSensors.getTempCByIndex(0);
  if (soilTemp == DEVICE_DISCONNECTED_C || soilTemp < -40.0) {
    soilTemp = 24.5; // Sensor disconnected fallback
  }

  int rawMoist = analogRead(PIN_MOISTURE);
  float soilMoist = calculateMoisturePercent(rawMoist);

  // 2. Autonomous Irrigation Logic (Edge Fallback)
  handleIrrigation(soilMoist);

  // 3. Periodic Cloud Telemetry Dispatch
  unsigned long now = millis();
  if (now - lastUploadTime >= UPLOAD_INTERVAL_MS) {
    lastUploadTime = now;
    sendTelemetry(soilTemp, soilMoist, rawMoist, isPumpActive);
  }

  delay(200); // Gentle loop yield
}

// ==============================================================================
// 5. HELPER FUNCTIONS
// ==============================================================================

// Moisture Calibration Helper
float calculateMoisturePercent(int rawADC) {
  if (rawADC >= DRY_ADC_VALUE) return 0.0;
  if (rawADC <= WET_ADC_VALUE) return 100.0;
  float pct = ((float)(DRY_ADC_VALUE - rawADC) / (float)(DRY_ADC_VALUE - WET_ADC_VALUE)) * 100.0;
  return constrain(pct, 0.0, 100.0);
}

// Local Autonomous Relay Control
void handleIrrigation(float currentMoisture) {
  if (!isPumpActive && currentMoisture <= PUMP_ON_THRESHOLD) {
    digitalWrite(PIN_RELAY, HIGH);
    isPumpActive = true;
    pumpStartTime = millis();
    Serial.printf("💧 [PUMP ACTIVATED] Soil moisture (%.1f%%) <= Threshold (%.1f%%)\n", currentMoisture, PUMP_ON_THRESHOLD);
  } else if (isPumpActive) {
    bool moistureSatisfied = (currentMoisture >= PUMP_OFF_THRESHOLD);
    bool timeoutExceeded = (millis() - pumpStartTime >= MAX_PUMP_RUN_MS);

    if (moistureSatisfied || timeoutExceeded) {
      digitalWrite(PIN_RELAY, LOW);
      isPumpActive = false;
      if (timeoutExceeded) {
        Serial.println("⚠️ [PUMP STOPPED] Safety runtime limit reached (30s).");
      } else {
        Serial.printf("✅ [PUMP STOPPED] Target moisture satisfied (%.1f%% >= %.1f%%)\n", currentMoisture, PUMP_OFF_THRESHOLD);
      }
    }
  }
}

// HTTPS Telemetry Ingestion to cPanel
void sendTelemetry(float temp, float moist, int rawMoist, bool pumpState) {
  if (WiFi.status() != WL_CONNECTED) return;

  WiFiClientSecure client;
  client.setInsecure(); // Bypass SSL fingerprint check for seamless connectivity

  HTTPClient https;
  if (https.begin(client, SERVER_URL)) {
    https.addHeader("Content-Type", "application/json");
    https.addHeader("X-Device-ID", DEVICE_ID);
    https.addHeader("X-API-Key", API_KEY);

    // Build JSON Payload
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
      Serial.printf("📡 [CLOUD SYNC OK] Temp: %.1f°C | Moisture: %.1f%% | Pump: %s | RSSI: %d dBm\n",
                    temp, moist, pumpState ? "ON" : "OFF", WiFi.RSSI());
    } else {
      String response = https.getString();
      Serial.printf("❌ [CLOUD SYNC ERROR] HTTP %d: %s\n", httpCode, response.c_str());
    }
    https.end();
  }
}

// Wi-Fi Connection Manager
void connectWiFi() {
  Serial.printf("📡 Connecting to Wi-Fi SSID: %s ", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 25) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ Wi-Fi Connected!");
    Serial.print("📱 Node IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("📶 Signal Strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n⚠️ Wi-Fi Connection Timeout. Will retry in loop...");
  }
}
