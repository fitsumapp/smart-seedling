"""Unit tests for Smart Seedling database models, constraints, and validation."""

from datetime import date, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from accounts.models import User, UserRole, ActivityLog
from nursery.models import Nursery, NurseryZone, SeedlingBatch, SeedlingStatus
from devices.models import Device, DeviceSetting, DeviceStatus
from monitoring.models import SensorReading
from alerts.models import Alert, AlertType, AlertSeverity


class ModelValidationTestCase(TestCase):
    def setUp(self):
        # Create test nursery and zone
        self.nursery = Nursery.objects.create(
            name="Green Valley Nursery",
            code="GVN-01",
            location="Greenhouse Alpha"
        )
        self.zone = NurseryZone.objects.create(
            nursery=self.nursery,
            name="Propagation Zone 1",
            code="ZONE-A"
        )

    def test_user_roles_and_permissions_logic(self):
        super_admin = User.objects.create_user(
            username="superadmin",
            password="password123",
            role=UserRole.SUPER_ADMIN,
            is_superuser=True
        )
        nursery_admin = User.objects.create_user(
            username="nurseryadmin",
            password="password123",
            role=UserRole.NURSERY_ADMIN,
            assigned_nursery=self.nursery
        )
        operator = User.objects.create_user(
            username="operator1",
            password="password123",
            role=UserRole.OPERATOR,
            assigned_nursery=self.nursery
        )

        self.assertTrue(super_admin.is_super_admin)
        self.assertTrue(super_admin.is_nursery_admin)
        self.assertTrue(super_admin.is_operator)
        self.assertTrue(super_admin.can_manage_nursery(self.nursery))

        self.assertFalse(nursery_admin.is_super_admin)
        self.assertTrue(nursery_admin.is_nursery_admin)
        self.assertTrue(nursery_admin.is_operator)
        self.assertTrue(nursery_admin.can_manage_nursery(self.nursery))

        other_nursery = Nursery.objects.create(name="Other Nursery", code="OTH-01")
        self.assertFalse(nursery_admin.can_manage_nursery(other_nursery))

        self.assertFalse(operator.is_super_admin)
        self.assertFalse(operator.is_nursery_admin)
        self.assertTrue(operator.is_operator)

    def test_activity_log_helper(self):
        user = User.objects.create_user(username="actor", password="password123")
        log = ActivityLog.log(
            action="TEST_ACTION",
            user=user,
            details={"key": "value"},
            ip_address="127.0.0.1"
        )
        self.assertEqual(log.action, "TEST_ACTION")
        self.assertEqual(log.user, user)
        self.assertEqual(log.details.get("key"), "value")

    def test_nursery_and_zone_uniqueness(self):
        from django.db import transaction
        # Nursery code is upper-cased and unique
        duplicate_nursery = Nursery(name="Duplicate", code="gvn-01")
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                duplicate_nursery.save()

        # Zone code within same nursery must be unique
        duplicate_zone = NurseryZone(nursery=self.nursery, name="Zone A Clone", code="ZONE-A")
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                duplicate_zone.save()


    def test_seedling_batch_creation_and_qr_token(self):
        from django.utils import timezone
        today = timezone.now().date()
        batch = SeedlingBatch.objects.create(
            nursery=self.nursery,
            nursery_zone=self.zone,
            batch_code="BATCH-2026-TOM-001",
            plant_name="San Marzano Tomato",
            species="Solanum lycopersicum",
            planting_date=today - timedelta(days=10),
            quantity=50,
            status=SeedlingStatus.GROWING
        )
        self.assertTrue(bool(batch.qr_token))
        self.assertEqual(len(batch.qr_token), 32)
        self.assertEqual(batch.age_days, 10)


    def test_device_api_key_generation_and_verification(self):
        device = Device(
            nursery_zone=self.zone,
            device_id="ESP32-001",
            name="Bench 1 Controller"
        )
        raw_key = device.save()
        self.assertIsNotNone(raw_key)
        self.assertTrue(device.verify_api_key(raw_key))
        self.assertFalse(device.verify_api_key("wrong_key_12345"))

        # Verify auto-created settings and status
        self.assertIsNotNone(device.settings)
        self.assertIsNotNone(device.status)
        self.assertEqual(device.settings.pump_on_threshold, 30.0)
        self.assertEqual(device.settings.pump_off_threshold, 50.0)

    def test_device_setting_threshold_validation(self):
        device = Device.objects.create(
            nursery_zone=self.zone,
            device_id="ESP32-002",
            name="Bench 2 Controller"
        )
        settings = device.settings
        settings.pump_on_threshold = 60.0
        settings.pump_off_threshold = 40.0  # Invalid: OFF threshold <= ON threshold

        with self.assertRaises(ValidationError):
            settings.save()

    def test_sensor_reading_creation(self):
        device = Device.objects.create(
            nursery_zone=self.zone,
            device_id="ESP32-003",
            name="Bench 3 Controller"
        )
        reading = SensorReading.objects.create(
            device=device,
            soil_temperature=24.5,
            soil_moisture=45.0,
            soil_moisture_raw=2300,
            pump_status=False
        )
        self.assertEqual(reading.device, device)
        self.assertEqual(reading.soil_moisture, 45.0)
