"""Unit tests for automatic alert generation and deduplication."""

from django.test import TestCase
from devices.models import Device
from nursery.models import Nursery, NurseryZone
from monitoring.models import SensorReading
from alerts.models import Alert, AlertType, AlertSeverity
from alerts.services import AlertService


class AlertServiceTestCase(TestCase):
    def setUp(self):
        self.nursery = Nursery.objects.create(name="Nursery Gamma", code="NUR-G")
        self.zone = NurseryZone.objects.create(nursery=self.nursery, name="Zone 1", code="Z1")
        self.device = Device(nursery_zone=self.zone, device_id="ESP32-ALERT-01", name="Alert Test Unit")
        self.device.save()

        # Target threshold: ON at 30%, OFF at 50%
        self.device.settings.pump_on_threshold = 30.0
        self.device.settings.pump_off_threshold = 50.0
        self.device.settings.save()

    def test_low_soil_moisture_triggers_alert(self):
        reading = SensorReading.objects.create(
            device=self.device,
            soil_temperature=22.0,
            soil_moisture=15.0,  # Below 30%
            soil_moisture_raw=3100,
            pump_status=True
        )

        alerts = AlertService.evaluate_reading(reading)
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.alert_type, AlertType.LOW_SOIL_MOISTURE)
        self.assertFalse(alert.is_resolved)

    def test_alert_deduplication(self):
        # First low reading triggers alert
        reading1 = SensorReading.objects.create(
            device=self.device,
            soil_temperature=22.0,
            soil_moisture=20.0,
            soil_moisture_raw=3000,
            pump_status=True
        )
        AlertService.evaluate_reading(reading1)

        # Second low reading within cooldown/active period should NOT create another open alert
        reading2 = SensorReading.objects.create(
            device=self.device,
            soil_temperature=22.5,
            soil_moisture=19.0,
            soil_moisture_raw=3050,
            pump_status=True
        )
        alerts2 = AlertService.evaluate_reading(reading2)
        self.assertEqual(len(alerts2), 0)

        # Confirm only 1 unresolved alert exists
        total_open_alerts = Alert.objects.filter(device=self.device, is_resolved=False).count()
        self.assertEqual(total_open_alerts, 1)

    def test_high_temperature_triggers_alert(self):
        reading = SensorReading.objects.create(
            device=self.device,
            soil_temperature=42.5,  # Exceeds 38°C
            soil_moisture=45.0,
            soil_moisture_raw=2200,
            pump_status=False
        )
        alerts = AlertService.evaluate_reading(reading)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, AlertType.HIGH_SOIL_TEMPERATURE)

    def test_sensor_error_triggers_alert(self):
        reading = SensorReading.objects.create(
            device=self.device,
            soil_temperature=-127.0,  # Disconnected DS18B20
            soil_moisture=45.0,
            soil_moisture_raw=2200,
            pump_status=False
        )
        alerts = AlertService.evaluate_reading(reading)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, AlertType.SENSOR_ERROR)

    def test_auto_resolution_when_condition_cleared(self):
        # Trigger low moisture alert
        reading1 = SensorReading.objects.create(
            device=self.device,
            soil_temperature=22.0,
            soil_moisture=20.0,
            soil_moisture_raw=3000,
            pump_status=True
        )
        AlertService.evaluate_reading(reading1)
        self.assertTrue(Alert.objects.filter(device=self.device, alert_type=AlertType.LOW_SOIL_MOISTURE, is_resolved=False).exists())

        # Follow-up healthy reading (moisture = 45%) should auto-resolve the alert
        reading2 = SensorReading.objects.create(
            device=self.device,
            soil_temperature=22.0,
            soil_moisture=45.0,
            soil_moisture_raw=2200,
            pump_status=False
        )
        AlertService.evaluate_reading(reading2)
        self.assertFalse(Alert.objects.filter(device=self.device, alert_type=AlertType.LOW_SOIL_MOISTURE, is_resolved=False).exists())
        self.assertTrue(Alert.objects.filter(device=self.device, alert_type=AlertType.LOW_SOIL_MOISTURE, is_resolved=True).exists())
