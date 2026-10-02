# Smart Seedling REST API Documentation (v1)

Base URL: `http://<server-host>/api/v1/`

All endpoints return JSON responses. Errors follow a standardized error envelope:
```json
{
  "success": false,
  "error": "Error description or dictionary of validation errors",
  "status_code": 400
}
```

---

## Device Authentication

Devices authenticate using one of the following methods:

### Method A (Recommended): Custom HTTP Headers
```http
X-Device-ID: ESP32-001
X-API-Key: <secret_api_key>
```

### Method B: Authorization Header
```http
Authorization: DeviceKey ESP32-001:<secret_api_key>
```

---

## Endpoints

### 1. Ingest Sensor Telemetry
* **Endpoint**: `/api/v1/device/readings/`
* **Method**: `POST`
* **Authentication**: Device Credentials (Headers or Authorization)
* **Headers**: `Content-Type: application/json`

#### Request Body
```json
{
  "device_id": "ESP32-001",
  "soil_temperature": 24.81,
  "soil_moisture": 42.0,
  "soil_moisture_raw": 2450,
  "pump_status": true,
  "rssi": -58,
  "firmware_version": "1.0.0",
  "device_timestamp": null
}
```

#### Validation Rules
| Field | Type | Required | Constraints |
|---|---|---|---|
| `device_id` | string | Yes | Must match authenticated device ID |
| `soil_temperature` | float | Yes | -20.0 to 80.0 °C |
| `soil_moisture` | float | Yes | 0.0 to 100.0 % |
| `soil_moisture_raw` | integer | Yes | 0 to 4095 (12-bit ADC) |
| `pump_status` | boolean | Yes | `true` (ON) or `false` (OFF) |
| `rssi` | integer | No | -120 to 0 dBm |
| `firmware_version` | string | No | Max 30 chars |
| `device_timestamp` | ISO8601 | No | Nullable |

#### Response (`201 Created`)
```json
{
  "success": true,
  "message": "reading_saved",
  "server_time": "2026-08-18T02:04:35.568122+00:00"
}
```

---

### 2. Fetch Device Irrigation Settings
* **Endpoint**: `/api/v1/device/settings/`
* **Method**: `GET`
* **Authentication**: Device Credentials

#### Response (`200 OK`)
```json
{
  "pump_on_threshold": 30.0,
  "pump_off_threshold": 50.0,
  "reading_interval_seconds": 2,
  "upload_interval_seconds": 10,
  "automatic_mode": true,
  "max_pump_runtime_seconds": 30
}
```

---

### 3. Device Heartbeat Ping
* **Endpoint**: `/api/v1/device/heartbeat/`
* **Method**: `POST`
* **Authentication**: Device Credentials
* **Headers**: `Content-Type: application/json`

#### Request Body
```json
{
  "rssi": -64,
  "firmware_version": "1.0.1",
  "operational_state": "IDLE"
}
```

#### Response (`200 OK`)
```json
{
  "success": true,
  "message": "heartbeat_acknowledged",
  "server_time": "2026-08-18T02:05:18.546911+00:00"
}
```
