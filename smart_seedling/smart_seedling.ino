/*
 * ==============================================================================
 * Smart Seedling Nursery IoT - Production ESP32 Firmware with Relay Support
 * ==============================================================================
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <WiFiManager.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>

const char* SERVER_URL    = "https://seedling.acrmatech.com/api/v1/device/readings/";
const char* DEVICE_ID     = "ESP32-001";
const char* API_KEY       = "secret-esp32-demo-api-key-2026";
const char* FIRMWARE_VER  = "1.0.0";

#define PIN_DS18B20       4
#define PIN_MOISTURE      34
#define PIN_RELAY         27

// አብዛኞቹ የ Arduino ሪሌዮች Active-LOW ስለሆኑ true ይደረጋል
const bool RELAY_ACTIVE_LOW = true;

const int DRY_ADC_VALUE   = 3200;
const int WET_ADC_VALUE   = 1350;

float PUMP_ON_THRESHOLD   = 30.0;  // ከ 30% በታች ሲሆን ፓምፑ ይበራል
float PUMP_OFF_THRESHOLD  = 50.0;  // 50% ሲደርስ ፓምፑ ይጠፋል
unsigned long MAX_PUMP_RUN_MS = 30000;

OneWire oneWire(PIN_DS18B20);
DallasTemperature tempSensors(&oneWire);

unsigned long lastUploadTime = 0;
const unsigned long UPLOAD_INTERVAL_MS = 2000;
unsigned long pumpStartTime = 0;
bool isPumpActive = false;

// ሪሌዩን በትክክል ማብሪያና ማጥፊያ ፈንክሽን
void setPumpHardware(bool turnOn) {
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(PIN_RELAY, turnOn ? LOW : HIGH);
  } else {
    digitalWrite(PIN_RELAY, turnOn ? HIGH : LOW);
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n🌱 Smart Seedling ESP32 Node Booting...");

  pinMode(PIN_RELAY, OUTPUT);
  setPumpHardware(false); // ፓምፑ ጠፍቶ እንዲጀምር

  // የሪሌይ የሙከራ ድምፅ (Startup Click Test)
  Serial.println("⚡ Testing Relay Click (1 sec ON then OFF)...");
  setPumpHardware(true);
  delay(800);
  setPumpHardware(false);
  Serial.println("⚡ Relay Test Complete.");

  pinMode(PIN_MOISTURE, INPUT);
  tempSensors.begin();

  WiFiManager wm;
  wm.autoConnect("SmartSeedling-Setup");
  Serial.println("\n✅ Wi-Fi Connected!");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    delay(100);
    return;
  }

  tempSensors.requestTemperatures();
  float soilTemp = tempSensors.getTempCByIndex(0);
  if (soilTemp == DEVICE_DISCONNECTED_C || soilTemp < -40.0) {
    soilTemp = 24.5;
  }

  int rawMoist = analogRead(PIN_MOISTURE);
  float soilMoist = calculateMoisturePercent(rawMoist);

  handleIrrigation(soilMoist);

  unsigned long now = millis();
  if (now - lastUploadTime >= UPLOAD_INTERVAL_MS) {
    lastUploadTime = now;
    sendTelemetry(soilTemp, soilMoist, rawMoist, isPumpActive);
  }

  delay(100);
}

float calculateMoisturePercent(int rawADC) {
  if (rawADC >= DRY_ADC_VALUE) return 0.0;
  if (rawADC <= WET_ADC_VALUE) return 100.0;
  float pct = ((float)(DRY_ADC_VALUE - rawADC) / (float)(DRY_ADC_VALUE - WET_ADC_VALUE)) * 100.0;
  return constrain(pct, 0.0, 100.0);
}

void handleIrrigation(float currentMoisture) {
  if (!isPumpActive && currentMoisture <= PUMP_ON_THRESHOLD) {
    setPumpHardware(true);
    isPumpActive = true;
    pumpStartTime = millis();
    Serial.printf("💧 [PUMP ON] Soil Moisture (%.1f%%) <= Threshold (%.1f%%)\n", currentMoisture, PUMP_ON_THRESHOLD);
  } else if (isPumpActive) {
    bool moistureSatisfied = (currentMoisture >= PUMP_OFF_THRESHOLD);
    bool timeoutExceeded = (millis() - pumpStartTime >= MAX_PUMP_RUN_MS);

    if (moistureSatisfied || timeoutExceeded) {
      setPumpHardware(false);
      isPumpActive = false;
      if (timeoutExceeded) {
        Serial.println("⚠️ [PUMP OFF] 30-second safety cutoff reached.");
      } else {
        Serial.printf("✅ [PUMP OFF] Target reached (%.1f%% >= %.1f%%)\n", currentMoisture, PUMP_OFF_THRESHOLD);
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
