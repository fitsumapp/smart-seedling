"""Integration tests for ESP32 Device REST API endpoints."""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from devices.models import Device
from nursery.models import Nursery, NurseryZone
from monitoring.models import SensorReading


class DeviceAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create Nursery and Zone
        self.nursery = Nursery.objects.create(name="Nursery Beta", code="NUR-B")
        self.zone = NurseryZone.objects.create(nursery=self.nursery, name="Zone 1", code="Z1")

        # Create Active Device
        self.device = Device(
            nursery_zone=self.zone,
            device_id="ESP32-001",
            name="Alpha Bench Unit"
        )
        self.api_key = self.device.save()

        # Create Inactive Device
        self.inactive_device = Device(
            nursery_zone=self.zone,
            device_id="ESP32-INACTIVE",
            name="Decommissioned Unit",
            is_active=False
        )
        self.inactive_api_key = self.inactive_device.save()

    def test_post_sensor_reading_success(self):
        url = '/api/v1/device/readings/'
        payload = {
            "device_id": "ESP32-001",
            "soil_temperature": 24.81,
            "soil_moisture": 42.0,
            "soil_moisture_raw": 2450,
            "pump_status": True,
            "rssi": -58,
            "firmware_version": "1.0.0"
        }

        response = self.client.post(
            url,
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID="ESP32-001",
            HTTP_X_API_KEY=self.api_key
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'reading_saved')
        self.assertIn('server_time', response.data)

        # Verify reading saved to database
        reading = SensorReading.objects.filter(device=self.device).first()
        self.assertIsNotNone(reading)
        self.assertEqual(reading.soil_temperature, 24.81)
        self.assertEqual(reading.soil_moisture, 42.0)
        self.assertEqual(reading.soil_moisture_raw, 2450)
        self.assertTrue(reading.pump_status)

        # Verify device status updated
        self.device.refresh_from_db()
        self.assertIsNotNone(self.device.last_seen)
        self.assertEqual(self.device.status.rssi, -58)
        self.assertEqual(self.device.status.operational_state, 'IRRIGATING')

    def test_post_reading_with_authorization_header(self):
        url = '/api/v1/device/readings/'
        payload = {
            "device_id": "ESP32-001",
            "soil_temperature": 23.5,
            "soil_moisture": 38.0,
            "soil_moisture_raw": 2550,
            "pump_status": False
        }

        # Authorization: DeviceKey <device_id>:<api_key>
        auth_header = f"DeviceKey ESP32-001:{self.api_key}"
        response = self.client.post(
            url,
            data=payload,
            format='json',
            HTTP_AUTHORIZATION=auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_reading_invalid_api_key(self):
        url = '/api/v1/device/readings/'
        payload = {
            "device_id": "ESP32-001",
            "soil_temperature": 24.0,
            "soil_moisture": 40.0,
            "soil_moisture_raw": 2400,
            "pump_status": False
        }

        response = self.client.post(
            url,
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID="ESP32-001",
            HTTP_X_API_KEY="invalid_secret_key"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])

    def test_post_reading_unknown_device(self):
        url = '/api/v1/device/readings/'
        payload = {
            "device_id": "ESP32-NONEXISTENT",
            "soil_temperature": 24.0,
            "soil_moisture": 40.0,
            "soil_moisture_raw": 2400,
            "pump_status": False
        }

        response = self.client.post(
            url,
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID="ESP32-NONEXISTENT",
            HTTP_X_API_KEY=self.api_key
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_reading_inactive_device(self):
        url = '/api/v1/device/readings/'
        payload = {
            "device_id": "ESP32-INACTIVE",
            "soil_temperature": 24.0,
            "soil_moisture": 40.0,
            "soil_moisture_raw": 2400,
            "pump_status": False
        }

        response = self.client.post(
            url,
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID="ESP32-INACTIVE",
            HTTP_X_API_KEY=self.inactive_api_key
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_reading_mismatching_payload_device_id(self):
        url = '/api/v1/device/readings/'
        payload = {
            "device_id": "ESP32-SPOOFED-ID",
            "soil_temperature": 24.0,
            "soil_moisture": 40.0,
            "soil_moisture_raw": 2400,
            "pump_status": False
        }

        response = self.client.post(
            url,
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID="ESP32-001",
            HTTP_X_API_KEY=self.api_key
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_reading_validation_errors(self):
        url = '/api/v1/device/readings/'

        # Soil moisture out of bounds (> 100)
        invalid_payload_1 = {
            "device_id": "ESP32-001",
            "soil_temperature": 24.0,
            "soil_moisture": 150.0,
            "soil_moisture_raw": 2400,
            "pump_status": False
        }
        res1 = self.client.post(url, invalid_payload_1, format='json', HTTP_X_DEVICE_ID="ESP32-001", HTTP_X_API_KEY=self.api_key)
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        # Negative soil moisture
        invalid_payload_2 = {
            "device_id": "ESP32-001",
            "soil_temperature": 24.0,
            "soil_moisture": -10.0,
            "soil_moisture_raw": 2400,
            "pump_status": False
        }
        res2 = self.client.post(url, invalid_payload_2, format='json', HTTP_X_DEVICE_ID="ESP32-001", HTTP_X_API_KEY=self.api_key)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        # Unrealistic soil temperature (> 80)
        invalid_payload_3 = {
            "device_id": "ESP32-001",
            "soil_temperature": 120.0,
            "soil_moisture": 50.0,
            "soil_moisture_raw": 2400,
            "pump_status": False
        }
        res3 = self.client.post(url, invalid_payload_3, format='json', HTTP_X_DEVICE_ID="ESP32-001", HTTP_X_API_KEY=self.api_key)
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_device_settings(self):
        url = '/api/v1/device/settings/'
        response = self.client.get(
            url,
            HTTP_X_DEVICE_ID="ESP32-001",
            HTTP_X_API_KEY=self.api_key
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pump_on_threshold'], 30.0)
        self.assertEqual(response.data['pump_off_threshold'], 50.0)
        self.assertEqual(response.data['reading_interval_seconds'], 2)
        self.assertEqual(response.data['upload_interval_seconds'], 10)
        self.assertTrue(response.data['automatic_mode'])
        self.assertEqual(response.data['max_pump_runtime_seconds'], 30)

    def test_post_device_heartbeat(self):
        url = '/api/v1/device/heartbeat/'
        payload = {
            "rssi": -65,
            "firmware_version": "1.0.1",
            "operational_state": "IDLE"
        }

        response = self.client.post(
            url,
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID="ESP32-001",
            HTTP_X_API_KEY=self.api_key
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'heartbeat_acknowledged')

        self.device.refresh_from_db()
        self.assertEqual(self.device.firmware_version, "1.0.1")
        self.assertEqual(self.device.status.rssi, -65)
        self.assertEqual(self.device.status.operational_state, "IDLE")
