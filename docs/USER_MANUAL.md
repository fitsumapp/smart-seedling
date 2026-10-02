# 🌱 Smart Seedling IoT Platform — የተጠቃሚ መመሪያ / User Manual

> **Project Name:** Smart Seedling Nursery Monitoring & Automated Irrigation Control System  
> **Version:** 1.0 Production-Ready  
> **Languages Included:** አማርኛ (Amharic) & English  

---

# ማውጫ / Table of Contents

* [ክፍል ፩፡ የተሟላ የአማርኛ የተጠቃሚ መመሪያ (Amharic User Manual)](#ክፍል-፩-የተሟላ-የአማርኛ-የተጠቃሚ-መመሪያ)
  * [1. የሲስተሙ አጠቃላይ ገጽታና አላማ](#1-የሲስተሙ-አጠቃላይ-ገጽታና-አላማ)
  * [2. የተጠቃሚዎች የስልጣን እርከኖች](#2-የተጠቃሚዎች-የስልጣን-እርከኖች)
  * [3. የሲስተሙ ዋና ዋና ክፍሎች አጠቃቀም](#3-የሲስተሙ-ዋና-ዋና-ክፍሎች-አጠቃቀም)
  * [4. የ ESP32 ሃርድዌርና ሽቦ አሰካክ](#4-የ-esp32-ሃርድዌርና-ሽቦ-አሰካክ)
  * [5. የክላውድ ዲፕሎይመንትና አውቶ-ዲፕሎይ](#5-የክላውድ-ዲፕሎይመንትና-አውቶ-ዲፕሎይ)
  * [6. ተደጋጋሚ ችግሮችና መፍትሔዎቻቸው](#6-ተደጋጋሚ-ችግሮችና-መፍትሔዎቻቸው)
* [SECTION II: Complete English User & Operator Manual](#section-ii-complete-english-user--operator-manual)
  * [1. System Overview & Architecture](#1-system-overview--architecture)
  * [2. User Roles & Permission Hierarchy](#2-user-roles--permission-hierarchy)
  * [3. Detailed Module-by-Module Guide](#3-detailed-module-by-module-guide)
  * [4. ESP32 Hardware Wiring & Pinout Guide](#4-esp32-hardware-wiring--pinout-guide)
  * [5. Cloud Deployment & CI/CD Automation](#5-cloud-deployment--cicd-automation)
  * [6. Troubleshooting & Diagnostics](#6-troubleshooting--diagnostics)

---

# ክፍል ፩፡ የተሟላ የአማርኛ የተጠቃሚ መመሪያ

## 1. የሲስተሙ አጠቃላይ ገጽታና አላማ

**Smart Seedling** ዘመናዊ የ **IoT (Internet of Things)** ቴክኖሎጂን በመጠቀም የችግኝ ማፍያ ማዕከላትን (Greenhouses & Nurseries) የአፈር እርጥበት እና ሙቀት 24/7 በመከታተል አውቶማቲክ የጠብታ መስኖ (Precision Drip Irrigation) የሚሰጥ እና ለእያንዳንዱ የችግኝ ማሰሮ ልዩ የ **QR Code ዲጂታል ፓስፖርት** የሚያዘጋጅ የተሟላ የድር መተግበሪያ ነው።

### አጠቃላይ የስራ ፍሰት (System Architecture Flow):
```
┌─────────────────────────┐       Wi-Fi / Internet       ┌───────────────────────────────┐
│     ESP32 Hardware      │ ───────────────────────────► │      Django REST API Server   │
│ • DS18B20 (Temp)        │  POST /api/v1/device/readings│ • Authentication & Validation │
│ • Capacitive Soil Moist │                              │ • Real-Time Alert Engine      │
│ • 5V Relay (Water Pump) │ ◄─────────────────────────── │ • Continuous Storage          │
└─────────────────────────┘  GET /api/v1/device/settings └──────────────┬────────────────┘
                                                                        │
                                   ┌────────────────────────────────────┴───────────────────────────────────┐
                                   ▼                                                                        ▼
                    ┌─────────────────────────────┐                                          ┌─────────────────────────────┐
                    │  Live Analytics Dashboard   │                                          │  Public QR Plant Passport   │
                    │ • 1.5s Ultra-Fast Polling   │                                          │ • Mobile-Friendly Profile   │
                    │ • Temperature & Moisture %  │                                          │ • Plant Age & Care Guide    │
                    │ • Pump Timeline Charts      │                                          │ • Printable Pot Stickers    │
                    └─────────────────────────────┘                                          └─────────────────────────────┘
```

---

## 2. የተጠቃሚዎች የስልጣን እርከኖች

ሲስተሙ 3 የተከፋፈሉ የስልጣን እርከኖች አሉት፡

| የስልጣን እርከን (Role) | የተጠቃሚ ስም / የይለፍ ቃል | ስልጣንና ኃላፊነት |
| :--- | :--- | :--- |
| **Super Admin** | `admin` / `admin1234` | ሙሉ ሲስተሙን መቆጣጠር፣ አዳዲስ ተጠቃሚዎችን መፍጠር፣ የሃርድዌር API ቁልፎችን ማመንጨት እና የደህንነት ሎጎችን ማየት። |
| **Nursery Administrator** | `nursery_admin` / `manager1234` | የተመደበለትን የችግኝ ጣቢያ ብቻ ማስተዳደር፤ ችግኞችንና ዞኖችን **Add, Edit, Delete** ማድረግ፣ የማጠጫ እርጥበት ህጎችን መቀየር እና ማስጠንቀቂያዎችን ማስተካከል። |
| **Operator** | `operator` / `staff1234` | ዳሽቦርድ እና የሴንሰር መረጃዎችን ብቻ መመልከት (Read-only)። |

---

## 3. የሲስተሙ ዋና ዋና ክፍሎች አጠቃቀም

### 3.1. የቀጥታ ዳሽቦርድ (Live Interactive Dashboard)
* **መግቢያ ሊንክ:** 👉 [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
* **ዋና ዋና ክፍሎች፡**
  1. **የአየር ሁኔታ ካርድ (Weather / Climate Sidebar)**፡ የቀጥታ የአፈር ሙቀት (`24.8°C`)፣ እርጥበት (`48.4%`)፣ እና የፓምፕ ሩጫ ሁኔታ ያሳያል።
  2. **ማጠቃለያ 4 ሳጥኖች**፡ የነቁ ማዕከላት፣ ኦንላይን የሆኑ የ ESP32 ቦርዶች፣ እያደጉ ያሉ ጠቅላላ ችግኞች ብዛት።
  3. **የ 24 ሰዓት የቴሌሜትሪ መስመር ቻርት**፡ የአፈር እርጥበት እና ሙቀት ውጣ ውረድ።
  4. **የችግኞች የእድገት ዶናት ቻርት**፡ በደረጃ የተከፋፈሉ (Germinating, Growing, Ready)።
  5. **የውሃ ማጠጣት ታሪክ (Pump Timeline)**፡ ፓምፑ በስንት ሰዓት እንደበራና እንደጠፋ።
  6. **⚡ "Test Live Feed" አዝራር**፡ ሲነኩት ወዲያውኑ አዲስ መረጃ አስገብቶ ቻርቶቹ ያለ ማኑዋል Refresh በቅጽበት በዓይንዎ እንዲንቀሳቀሱ ያደርጋል።

### 3.2. የችግኝ ባቾች እና የ QR Code ማተሚያ (Seedling Batches & QR Passports)
* **መግቢያ ሊንክ:** 👉 [http://127.0.0.1:8000/admin/nursery/seedlingbatch/](http://127.0.0.1:8000/admin/nursery/seedlingbatch/)
* **አዲስ ችግኝ ለመመዝገብ (How to Add):**
  1. ከላይ በቀኝ በኩል **`+ Add Seedling Batch`** የሚለውን ይጫኑ።
  2. የተክሉን ስም (ለምሳሌ `Tomato`)፣ ዝርያውን (`San Marzano`), ብዛቱን (`100`)፣ የተዘራበትን ቀን እና ዞኑን ይምረጡ።
  3. **"Save"** ሲጫኑ ሲስተሙ በራሱ ልዩ የ 32-ዲጂት `qr_token` እና የ QR ኮድ ያመነጫል።
* **ስቲከር ማተም እና ማየት (Print & View):**
  * **"📱 View Passport"** ሲጫኑ $\rightarrow$ ውብ የሆነውን የደንበኛ የዲጂታል ፓስፖርት ገጽ ያሳያል።
  * **"🖨️ Pot Sticker"** ሲጫኑ $\rightarrow$ ለችግኝ ማሰሮ የሚለጠፍ የ 600x350px ስቲከር አውርደው ያትማሉ።

### 3.3. የማጠጣት ህጎችና ቅንብሮች (Irrigation Settings & Thresholds)
* **መግቢያ ሊንክ:** 👉 [http://127.0.0.1:8000/admin/devices/devicesetting/](http://127.0.0.1:8000/admin/devices/devicesetting/)
* **የሚስተካከሉ ዋና ዋና ደንቦች፡**
  * **`Pump ON Threshold` (ለምሳሌ፡ 30%)**፡ የአፈሩ እርጥበት ከዚህ ቁጥር በታች ሲወርድ ፓምፑ በራሱ ይበራል።
  * **`Pump OFF Threshold` (ለምሳሌ፡ 50%)**፡ እርጥበቱ ይህንን ቁጥር ሲያልፍ ፓምፑ በራሱ ይጠፋል።
  * **`Reading Interval` (ለምሳሌ፡ 2 ሰከንድ)**፡ ESP32 ሴንሰሩን በየስንት ሰከንዱ ይለካ።
  * **`Upload Interval` (ለምሳሌ፡ 10 ሰከንድ)**፡ ዳታ ወደ ሰርቨሩ በየስንት ሰከንዱ ይላክ።
  * **`Max Pump Runtime` (ለምሳሌ፡ 30 ሰከንድ)**፡ ሴንሰር ቢበላሽ እንኳን ፓምፑ ከመጠን በላይ ሰርቶ እንዳያጥለቀልቅ የሚያግድ የደህንነት ወሰን።

### 3.4. የ ESP32 ሃርድዌር መቆጣጠሪያ (Device Management)
* **መግቢያ ሊንክ:** 👉 [http://127.0.0.1:8000/admin/devices/device/](http://127.0.0.1:8000/admin/devices/device/)
* **አጠቃቀም፡**
  * አዳዲስ የ ESP32 ቦርዶችን መመዝገብ።
  * የቦርዱን የኦንላይን ሁኔታ እና የ Wi-Fi ሲግናል ጥንካሬ (`-58 dBm`) በቅጽበት መከታተል።
  * ሚስጥራዊ የ **`API Key`** ማመንጨት (ይህ ቁልፍ በ ESP32 ኮድ ውስጥ ይገባል)።

### 3.5. የሴንሰር መረጃዎች ታሪክ (Sensor Telemetry Readings)
* **መግቢያ ሊንክ:** 👉 [http://127.0.0.1:8000/admin/monitoring/sensorreading/](http://127.0.0.1:8000/admin/monitoring/sensorreading/)
* **አጠቃቀም፡**
  * ከሃርድዌሩ የመጡ በሺዎች የሚቆጠሩ መረጃዎችን ቀንና ሰዓት መርጦ መመርመር።
  * ትክክለኛውን የአፈር ሙቀት፣ እርጥበት እና Raw ADC እሴት (1400 - 3200) ማየት።

### 3.6. የስርዓት ማስጠንቀቂያዎች (System Alerts & Warnings)
* **መግቢያ ሊንክ:** 👉 [http://127.0.0.1:8000/admin/alerts/alert/](http://127.0.0.1:8000/admin/alerts/alert/)
* **አውቶማቲክ ማስጠንቀቂያዎች፡**
  1. `LOW_SOIL_MOISTURE`፡ እርጥበት ከ 25% በታች ሲወርድ።
  2. `HIGH_SOIL_TEMPERATURE`፡ ሙቀት ከ 35°C በላይ ሲጨምር።
  3. `DEVICE_OFFLINE`፡ ESP32 ከኔትወርክ ሲቋረጥ።
  4. `SENSOR_ERROR`፡ የሴንሰር ሽቦ ሲነቀል ወይም የተሳሳተ ቁጥር ሲመጣ።
* **ማስተካከያ:** ችግሩ ሲፈታ አስተዳዳሪው መርጦ **"Mark as resolved"** ማድረግ ይችላል።

### 3.7. የችግኝ ማዕከላትና ዞኖች (Nurseries & Zones)
* **መግቢያ ሊንክ:** 👉 [http://127.0.0.1:8000/admin/nursery/nursery/](http://127.0.0.1:8000/admin/nursery/nursery/)
* **አጠቃቀም፡**
  * የችግኝ ማዕከላትን (Facilities) መመዝገብ።
  * በውስጣቸው ያሉትን ዞኖች/ቤንቾች (ለምሳሌ፡ *Zone A - Propagation Bench 1*) ማደራጀት።

---

## 4. የ ESP32 ሃርድዌርና ሽቦ አሰካክ

| አካል (Component) | የ ESP32 ፒን (Pin) | ተግባር / ማስታወሻ |
| :--- | :--- | :--- |
| **DS18B20 Temp Sensor** | **GPIO 4** | ከ 4.7kΩ Pull-up Resistor ጋር (Data $\rightarrow$ GPIO 4, VCC $\rightarrow$ 3.3V, GND $\rightarrow$ GND) |
| **Capacitive Moisture Sensor** | **GPIO 34** | Analog Input (AOUT $\rightarrow$ GPIO 34, VCC $\rightarrow$ 3.3V, GND $\rightarrow$ GND) |
| **5V Relay Module (Water Pump)**| **GPIO 27** | Active-LOW (IN $\rightarrow$ GPIO 27, VCC $\rightarrow$ 5V/VIN, GND $\rightarrow$ GND) |

---

## 5. የክላውድ ዲፕሎይመንትና አውቶ-ዲፕሎይ (CI/CD)

ሲስተሙ ለ **[Render.com](https://render.com/)** እና **PostgreSQL** ዝግጁ ሆኖ ተዘጋጅቷል (`render.yaml`, `Procfile`, `build.sh`)።

1. **ወደ GitHub የመጫኛ ትዕዛዞች፡**
   ```powershell
   git init
   git add .
   git commit -m "Smart Seedling Production Version"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/smart_seedling.git
   git push -u origin main
   ```
2. **አውቶ-ዲፕሎይ (Continuous Deployment):**
   * በ VS Code ወይም Antigravity IDE ላይ ማንኛውንም ለውጥ አድርገው **`git push`** ባደረጉ ቁጥር Render በራሱ በ 1 ደቂቃ ውስጥ አዲሱን ኮድ ይገነባል (Auto-Deploy ያደርጋል)።

---

## 6. ተደጋጋሚ ችግሮችና መፍትሔዎቻቸው (Troubleshooting)

| ችግር (Issue) | መንስኤ (Cause) | ፈጣን መፍትሔ (Solution) |
| :--- | :--- | :--- |
| **`HTTP Code: -1` በ Serial Monitor** | ESP32 እና ኮምፒውተሩ የተለያየ Wi-Fi ላይ ናቸው ወይም Firewall ፖርት 8000 ዘግቶታል | ሁለቱንም በአንድ Wi-Fi ያገናኙ፤ ፖርት 8000 በዊንዶውስ Firewall ይፍቀዱ። |
| **`HTTP Code: 401 Unauthorized`** | የ `API_KEY` ወይም `DEVICE_ID` መለያየት | በ Django Admin ውስጥ ያለውን ትክክለኛ API Key በ ESP32 ኮድ ላይ ይተኩ። |
| **የእርጥበት ቁጥር አይቀየርም** | የሴንሰር Calibration ዋጋዎች መስተካከል አለባቸው | በኮዱ ላይ `DRY_VALUE` (3200) እና `WET_VALUE` (1400) እንደየአፈሩ አይነት ያስተካክሉ። |

---
---

# SECTION II: Complete English User & Operator Manual

## 1. System Overview & Architecture

**Smart Seedling** is an end-to-end smart agriculture web application designed for commercial seedling nurseries, greenhouses, and precision propagation facilities. 

It pairs IoT microcontrollers (ESP32) equipped with capacitive soil moisture sensors and waterproof temperature probes to automatically actuate drip irrigation pumps, stream real-time telemetry to a cloud database, visualize environmental trends on a live web dashboard, and generate verifiable **QR Code Digital Plant Passports** for pot traceability.

### High-Level Architecture
1. **IoT Edge Layer (ESP32)**: Samples soil moisture and temperature every 2 seconds, autonomously activates relays when moisture drops below thresholds, and streams JSON telemetry every 10 seconds.
2. **Backend API Layer (Django & DRF)**: Ingests telemetry via secured HTTP/HTTPS endpoints (`X-Device-ID`, `X-API-Key`), triggers rule-based alerts, updates device health, and stores time-series data.
3. **Admin & Command Center (Django Unfold)**: A modern, role-based administration portal configured with the organic "Harvesta" green theme for managing facilities, batches, thresholds, and alerts.
4. **Live Analytics Dashboard**: A client-side Chart.js frontend with 1.5-second polling, smooth slide transitions, and live simulation triggers.
5. **Customer Plant Passport Portal**: Public, mobile-friendly landing pages accessible via pot QR codes without exposing administrative credentials.

---

## 2. User Roles & Permission Hierarchy

The system enforces strict Multi-Tier Role-Based Access Control (RBAC):

| Role Tier | Default Credentials | Permissions & Access Scope |
| :--- | :--- | :--- |
| **Super Admin** | `admin` / `admin1234` | Full global access across all facilities, hardware provisioning, user account lifecycle, and security audit logs. |
| **Nursery Administrator** | `nursery_admin` / `manager1234` | Scoped strictly to their assigned nursery facility. Full **Add, Edit, Delete, View** permissions for Seedling Batches, Nursery Zones, Irrigation Thresholds, Sensor Readings, and Alert Resolutions. |
| **Operator** | `operator` / `staff1234` | Read-only access for monitoring live telemetry and reviewing alerts without editing privileges. |

---

## 3. Detailed Module-by-Module Guide

### 3.1. Live Interactive Dashboard
* **Access URL:** 👉 [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
* **Key Components:**
  * **Microclimate Sidebar Card**: Displays real-time temperature (`°C`), moisture (`%`), active pump state, and relative packet timestamps (`2s ago`).
  * **Top 4 Metric Summary Boxes**: Tracks total active nurseries, connected ESP32 nodes, growing seedlings, and active alerts.
  * **24-Hour Telemetry Line Chart**: Dual-axis curve plotting Soil Moisture (%) alongside Soil Temperature (°C).
  * **Seedling Life Stage Donut Chart**: Visualizes batch distribution across *Germinating*, *Growing*, and *Ready for Market* phases.
  * **Irrigation Activity Timeline**: Bottom chart detailing pump on/off durations over time.
  * **⚡ "Test Live Feed" Button**: Injects dynamic simulation readings for immediate real-time visual validation without physical hardware.

---

### 3.2. Seedling Batches & QR Pot Passports
* **Access URL:** 👉 [http://127.0.0.1:8000/admin/nursery/seedlingbatch/](http://127.0.0.1:8000/admin/nursery/seedlingbatch/)
* **Registering a New Batch:**
  1. Click **`+ Add Seedling Batch`** in the top right.
  2. Input Common Plant Name (e.g., *San Marzano Tomato*), Variety (*San Marzano 2*), Species (*Solanum lycopersicum*), Quantity (*100*), Planting Date, and Assigned Nursery Zone.
  3. Click **Save**. The system automatically generates a unique 32-character hexadecimal `qr_token` and high-resolution PNG QR code.
* **Printing Pot Labels:**
  * Click **`🖨️ Pot Sticker`** to download a 600x350px high-resolution printable label complete with plant metadata, facility branding, and scannable QR code.
* **Public Customer Page:**
  * Click **`📱 View Passport`** (e.g., `/plant/<qr_token>/`) to view the mobile-optimized profile displaying plant age, microclimate history, and home care guides.

---

### 3.3. Irrigation Settings & Precision Thresholds
* **Access URL:** 👉 [http://127.0.0.1:8000/admin/devices/devicesetting/](http://127.0.0.1:8000/admin/devices/devicesetting/)
* **Configurable Threshold Parameters:**
  * **`Pump ON Threshold` (Default: 30%)**: Soil moisture level below which the irrigation pump activates.
  * **`Pump OFF Threshold` (Default: 50%)**: Moisture level at which irrigation ceases.
  * **`Reading Interval` (Default: 2s)**: Sensor sampling frequency on the ESP32.
  * **`Upload Interval` (Default: 10s)**: Telemetry HTTP POST frequency to the Django server.
  * **`Max Pump Runtime` (Default: 30s)**: Safety cutoff mechanism preventing waterlogging or pump dry-run.

---

### 3.4. ESP32 Hardware Device Management
* **Access URL:** 👉 [http://127.0.0.1:8000/admin/devices/device/](http://127.0.0.1:8000/admin/devices/device/)
* **Key Features:**
  * Register new hardware units with unique Hardware IDs (e.g., `ESP32-001`).
  * Generate and regenerate secure SHA-256 hashed API keys.
  * Monitor live connection status (`ONLINE` vs `OFFLINE`) and Wi-Fi signal strength (`RSSI dBm`).

---

### 3.5. Sensor Telemetry Logs & Data Stream
* **Access URL:** 👉 [http://127.0.0.1:8000/admin/monitoring/sensorreading/](http://127.0.0.1:8000/admin/monitoring/sensorreading/)
* **Features:**
  * Historical audit log of every sensor packet received.
  * Filter by date ranges, pump activation state, and assigned facility.
  * Inspect calibrated percentages alongside raw 12-bit ADC values (1400–3200).

---

### 3.6. System Alerts & Anomaly Management
* **Access URL:** 👉 [http://127.0.0.1:8000/admin/alerts/alert/](http://127.0.0.1:8000/admin/alerts/alert/)
* **Automated Alert Types:**
  * `LOW_SOIL_MOISTURE`: Triggered when soil moisture drops below critical minimums.
  * `HIGH_SOIL_TEMPERATURE`: Triggered when temperature exceeds safe thresholds (e.g., >35°C).
  * `DEVICE_OFFLINE`: Raised when an ESP32 fails to post telemetry within expected windows.
  * `SENSOR_ERROR`: Detects disconnected pins or erratic sensor readings.
* **Resolution Workflow**: Administrators can select open alerts and execute the **"Mark selected alerts as resolved"** batch action.

---

## 4. ESP32 Hardware Wiring & Pinout Guide

### Wiring Schematic Table

| Hardware Component | ESP32 GPIO Pin | Wiring Description & Power Rails |
| :--- | :--- | :--- |
| **DS18B20 Temp Sensor** | **GPIO 4** | 1-Wire bus with 4.7kΩ pull-up resistor between Data and 3.3V. |
| **Capacitive Moisture Sensor** | **GPIO 34** | Analog Out (AOUT) connected to ADC1 Pin GPIO 34. Powered by 3.3V. |
| **5V Relay Module (Pump)** | **GPIO 27** | Active-LOW control input. VCC connected to VIN/5V rail, GND to GND. |

### C++ Firmware Configuration
In your Arduino firmware (`ESP32_Smart_Seedling.ino`), configure the server connection variables:
```cpp
const char* SERVER_URL = "http://10.125.32.249:8000/api/v1/device/readings/";
const char* DEVICE_ID  = "ESP32-001";
const char* API_KEY    = "secret-esp32-demo-api-key-2026";
```

---

## 5. Cloud Deployment & CI/CD Automation

The codebase includes production blueprints for **[Render.com](https://render.com/)** and managed **PostgreSQL** databases (`render.yaml`, `Procfile`, `build.sh`).

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Production Smart Seedling Release"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/smart_seedling.git
git push -u origin main
```

### 2. Automated Continuous Deployment (CI/CD)
* Connecting your repository to Render establishes automated webhook deployments: every `git push` committed locally triggers automated building, static asset compilation, database migration, and zero-downtime container replacement.

---

## 6. Troubleshooting & Diagnostics

| Diagnostic Symptom | Root Cause | Recommended Solution |
| :--- | :--- | :--- |
| **`HTTP Code: -1` in Serial Monitor** | ESP32 and host PC are on separate Wi-Fi subnets, or Windows Firewall is blocking inbound port 8000. | Connect both devices to the identical Wi-Fi network; open TCP port 8000 in Windows Firewall. |
| **`HTTP Code: 401 Unauthorized`** | API Key or Device ID mismatch between firmware and database. | Copy the active API Key from Django Admin into firmware `API_KEY` definition. |
| **Moisture readings static at 0% or 100%** | Sensor requires ADC calibration for local soil mix. | Adjust `DRY_VALUE` (e.g., 3200) and `WET_VALUE` (e.g., 1400) in Arduino firmware definitions. |

---

> 🌿 **Smart Seedling IoT Platform — Sustainable Precision Agriculture for the Future!**
