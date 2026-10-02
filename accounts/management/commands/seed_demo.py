"""Management command to seed realistic 24-hour telemetry history and multi-status batches."""

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from accounts.models import User, UserRole
from nursery.models import Nursery, NurseryZone, SeedlingBatch, SeedlingStatus
from devices.models import Device, DeviceSetting
from monitoring.models import SensorReading
from alerts.models import Alert, AlertType, AlertSeverity


class Command(BaseCommand):
    help = 'Seeds realistic 24-hour telemetry and batches for a rich, visual dashboard experience.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Generating realistic Smart Seedling telemetry data...'))

        # 1. Nursery
        nursery, _ = Nursery.objects.get_or_create(
            code='NUR-CENTRAL-01',
            defaults={
                'name': 'Greenleaf Research Greenhouse',
                'location': 'Sector 4, Facility Alpha',
                'description': 'Smart automated seedling propagation facility.'
            }
        )

        # 2. Super Admin User
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@smartseedling.local',
                'role': UserRole.SUPER_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin1234')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        # 3. Dedicated Nursery Administrator User
        nursery_admin, _ = User.objects.get_or_create(
            username='nursery_admin',
            defaults={
                'email': 'manager@smartseedling.local',
                'role': UserRole.NURSERY_ADMIN,
                'assigned_nursery': nursery,
                'is_staff': True,
                'is_superuser': False,
            }
        )
        nursery_admin.set_password('manager1234')
        nursery_admin.role = UserRole.NURSERY_ADMIN
        nursery_admin.assigned_nursery = nursery
        nursery_admin.is_staff = True
        nursery_admin.is_superuser = False
        nursery_admin.save()

        # Assign granular model permissions to nursery_admin
        target_models = [Nursery, NurseryZone, SeedlingBatch, Device, DeviceSetting, SensorReading, Alert]
        for model in target_models:
            ct = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=ct)
            nursery_admin.user_permissions.add(*perms)

        # 4. Nursery Zone
        zone, _ = NurseryZone.objects.get_or_create(
            nursery=nursery,
            code='ZONE-A',
            defaults={
                'name': 'High-Humidity Propagation Bench 1',
                'description': 'Automated microclimate and drip irrigation bench.'
            }
        )

        # 5. Device
        device, _ = Device.objects.get_or_create(
            device_id='ESP32-001',
            defaults={
                'name': 'Bench 1 Hydro-Node',
                'nursery_zone': zone,
                'firmware_version': '1.0.0',
                'is_active': True
            }
        )
        device.set_api_key('secret-esp32-demo-api-key-2026')
        device.last_seen = timezone.now()
        device.save()

        if hasattr(device, 'status'):
            device.status.last_seen = timezone.now()
            device.status.rssi = -58
            device.status.operational_state = 'IDLE'
            device.status.save()

        # 6. Multi-Status Seedling Batches for Donut Chart
        SeedlingBatch.objects.all().delete()
        today = timezone.now().date()
        
        SeedlingBatch.objects.create(
            nursery=nursery,
            nursery_zone=zone,
            batch_code='BATCH-2026-TOM-001',
            plant_name='San Marzano Tomato',
            variety='San Marzano 2',
            quantity=80,
            status=SeedlingStatus.GROWING,
            planting_date=today - timedelta(days=14),
            care_instructions='Maintain moisture 40-50%. Bright indirect sunlight.'
        )

        SeedlingBatch.objects.create(
            nursery=nursery,
            nursery_zone=zone,
            batch_code='BATCH-2026-PEP-002',
            plant_name='Bell Pepper',
            variety='California Wonder',
            quantity=40,
            status=SeedlingStatus.GERMINATING,
            planting_date=today - timedelta(days=5),
            care_instructions='Warm humidity. Water gently.'
        )

        SeedlingBatch.objects.create(
            nursery=nursery,
            nursery_zone=zone,
            batch_code='BATCH-2026-LET-003',
            plant_name='Butterhead Lettuce',
            variety='Buttercrunch',
            quantity=30,
            status=SeedlingStatus.READY,
            planting_date=today - timedelta(days=28),
            care_instructions='Ready for garden bed transplantation.'
        )

        # 7. Generate 24-Hour Telemetry
        SensorReading.objects.filter(device=device).delete()
        now = timezone.now()
        readings_to_create = []

        total_steps = 144
        interval_minutes = 10
        current_moisture = 44.0
        pump_state = False

        for i in range(total_steps):
            timestamp = now - timedelta(minutes=(total_steps - i) * interval_minutes)
            hour = timestamp.hour

            if 6 <= hour <= 18:
                temp_base = 24.0 + 4.5 * ((hour - 6) / 6 if hour <= 12 else (18 - hour) / 6)
            else:
                temp_base = 19.5 + random.uniform(-0.5, 0.5)

            temp = round(temp_base + random.uniform(-0.3, 0.3), 1)

            if pump_state:
                current_moisture += random.uniform(3.5, 6.0)
                if current_moisture >= 49.5:
                    pump_state = False
            else:
                current_moisture -= random.uniform(0.6, 1.4)
                if current_moisture <= 30.0:
                    pump_state = True

            current_moisture = max(26.0, min(56.0, current_moisture))
            moisture = round(current_moisture, 1)
            raw_adc = int(3200 - (moisture / 100.0) * (3200 - 1400))

            readings_to_create.append(
                SensorReading(
                    device=device,
                    soil_temperature=temp,
                    soil_moisture=moisture,
                    soil_moisture_raw=raw_adc,
                    pump_status=pump_state,
                    received_at=timestamp
                )
            )

        SensorReading.objects.bulk_create(readings_to_create)
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(readings_to_create)} telemetry readings, 3 seedling batches, and configured users (admin & nursery_admin)!'))
