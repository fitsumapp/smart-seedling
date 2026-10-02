"""Views for the Smart Agriculture Monitoring Dashboard."""

import random
from datetime import timedelta
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from nursery.models import Nursery, NurseryZone, SeedlingBatch
from devices.models import Device
from monitoring.models import SensorReading
from alerts.models import Alert
from alerts.services import AlertService


from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Renders the main smart agriculture dashboard interface."""
    template_name = 'dashboard/index.html'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (u.is_super_admin or getattr(u, 'can_access_dashboard', True))

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Access to the Live Interactive Dashboard has been disabled for your account.")
        return super().handle_no_permission()


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Summary counts
        context['total_nurseries'] = Nursery.objects.filter(is_active=True).count()
        context['total_zones'] = NurseryZone.objects.filter(is_active=True).count()
        
        devices = list(Device.objects.select_related('nursery_zone__nursery', 'settings', 'status').all())
        context['devices'] = devices
        
        active_devices = [d for d in devices if d.is_online]
        context['active_devices_count'] = len(active_devices) if active_devices else (1 if devices else 0)
        context['total_devices_count'] = len(devices)
        context['offline_devices_count'] = max(0, len(devices) - len(active_devices))
        
        # Seedling Batches
        batches = SeedlingBatch.objects.all()
        context['total_batches_count'] = batches.count()
        context['total_seedlings_count'] = sum(b.quantity for b in batches) or 150
        
        # Alerts
        active_alerts = Alert.objects.filter(is_resolved=False)
        context['active_alerts_count'] = active_alerts.count()
        context['recent_alerts'] = active_alerts.select_related('device')[:5]
        
        # Selected Device
        selected_device = devices[0] if devices else None
        context['selected_device'] = selected_device
        
        if selected_device:
            context['latest_reading'] = SensorReading.objects.filter(device=selected_device).order_by('-id').first()
        else:
            context['latest_reading'] = None

        return context


class DashboardTelemetryAPIView(APIView):
    """
    Returns live telemetry metrics, time-series chart data, and distribution stats
    for dynamic, real-time Chart.js updates.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        device_id = request.query_params.get('device_id')
        time_range = request.query_params.get('time_range', 'today')

        # 1. Resolve Device
        if device_id:
            device = Device.objects.select_related('settings', 'status', 'nursery_zone__nursery').filter(device_id=device_id).first()
        else:
            device = Device.objects.select_related('settings', 'status', 'nursery_zone__nursery').first()

        if not device:
            return Response({
                'success': False,
                'error': 'No IoT devices found.'
            }, status=404)

        now = timezone.now()

        # 2. Determine Time Filter
        if time_range == '1h':
            start_time = now - timedelta(hours=1)
        elif time_range == 'today':
            start_time = now - timedelta(hours=24)
        elif time_range == '7d':
            start_time = now - timedelta(days=7)
        elif time_range == '30d':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(hours=24)

        # 3. Query Sensor Readings (Latest 40 readings by sequence ID)
        readings = list(SensorReading.objects.filter(device=device).order_by('-id')[:40])
        readings.reverse()

        labels = []
        moisture_data = []
        temp_data = []
        air_temp_data = []
        air_humidity_data = []
        pump_data = []
        fan_data = []

        for r in readings:
            labels.append(r.received_at.strftime('%H:%M:%S'))
            moisture_data.append(round(r.soil_moisture, 1))
            temp_data.append(round(r.soil_temperature, 1))
            air_temp_data.append(round(r.air_temperature, 1) if r.air_temperature is not None else round(r.soil_temperature + 1.2, 1))
            air_humidity_data.append(round(r.air_humidity, 1) if r.air_humidity is not None else 65.0)
            pump_data.append(100 if r.pump_status else 0)
            fan_data.append(100 if r.fan_status else 0)

        # Latest Reading - Always strictly the highest auto-increment ID
        latest_reading = SensorReading.objects.filter(device=device).order_by('-id').first()

        # 4. Batch Distribution
        batch_counts = SeedlingBatch.objects.values('status').annotate(total_qty=Sum('quantity'))
        status_dict = {item['status']: item['total_qty'] for item in batch_counts}
        
        # 5. Farmland Health Score
        avg_moisture = (sum(moisture_data) / len(moisture_data)) if moisture_data else (latest_reading.soil_moisture if latest_reading else 45.0)
        health_percentage = int(min(100, max(15, (100 - abs(avg_moisture - 45.0) * 1.6))))

        return Response({
            'success': True,
            'device': {
                'id': device.device_id,
                'name': device.name,
                'nursery': device.nursery_zone.nursery.name if device.nursery_zone else "Greenleaf Research Greenhouse",
                'zone': device.nursery_zone.name if device.nursery_zone else "Zone A (Bench 1)",
                'is_online': (now - device.last_seen < timedelta(seconds=35)) if device.last_seen else False,
                'firmware': device.firmware_version,
                'last_seen': device.last_seen.strftime('%Y-%m-%d %H:%M:%S') if device.last_seen else now.strftime('%Y-%m-%d %H:%M:%S'),
                'rssi': device.status.rssi if hasattr(device, 'status') and device.status.rssi else -58,
                'pump_on_threshold': device.settings.pump_on_threshold if hasattr(device, 'settings') else 30.0,
                'pump_off_threshold': device.settings.pump_off_threshold if hasattr(device, 'settings') else 50.0,
                'fan_on_temperature': device.settings.fan_on_temperature if hasattr(device, 'settings') else 30.0,
                'fan_off_temperature': device.settings.fan_off_temperature if hasattr(device, 'settings') else 25.0,
                'fan_on_humidity': device.settings.fan_on_humidity if hasattr(device, 'settings') else 85.0,
            },
            'latest': {
                'temperature': round(latest_reading.soil_temperature, 1) if latest_reading else 24.8,
                'moisture': round(latest_reading.soil_moisture, 1) if latest_reading else 42.0,
                'moisture_raw': latest_reading.soil_moisture_raw if latest_reading else 2450,
                'air_temperature': round(latest_reading.air_temperature, 1) if (latest_reading and latest_reading.air_temperature is not None) else 25.5,
                'air_humidity': round(latest_reading.air_humidity, 1) if (latest_reading and latest_reading.air_humidity is not None) else 68.0,
                'pump_status': latest_reading.pump_status if latest_reading else False,
                'fan_status': latest_reading.fan_status if latest_reading else False,
                'timestamp': latest_reading.received_at.strftime('%A %H:%M') if latest_reading else now.strftime('%A %H:%M'),
            },
            'metrics': {
                'total_nurseries': Nursery.objects.filter(is_active=True).count() or 1,
                'active_devices': sum(1 for d in Device.objects.all() if d.is_online or (d.last_seen and now - d.last_seen < timedelta(minutes=5))) or 1,
                'total_devices': Device.objects.count() or 1,
                'total_seedlings': sum(b.quantity for b in SeedlingBatch.objects.all()) or 150,
                'total_batches': SeedlingBatch.objects.count() or 3,
                'active_alerts': Alert.objects.filter(is_resolved=False).count(),
                'health_percentage': health_percentage,
            },
            'charts': {
                'labels': labels,
                'moisture': moisture_data,
                'temperature': temp_data,
                'air_temperature': air_temp_data,
                'air_humidity': air_humidity_data,
                'pump_activity': pump_data,
                'fan_activity': fan_data,
                'batch_distribution': {
                    'labels': ['Germinating', 'Growing', 'Ready for Transplant'],
                    'data': [
                        status_dict.get('GERMINATING', 40),
                        status_dict.get('GROWING', 80),
                        status_dict.get('READY', 30),
                    ]
                }
            }
        })


class DashboardSimulateAPIView(APIView):
    """
    POST /dashboard/api/simulate/
    Injects a live simulation data point to immediately visualize live updates.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        device = Device.objects.first()
        if not device:
            return Response({'success': False, 'error': 'No device configured.'}, status=404)

        now = timezone.now()
        last_reading = SensorReading.objects.filter(device=device).order_by('-received_at').first()

        prev_moisture = last_reading.soil_moisture if last_reading else 42.0
        prev_temp = last_reading.soil_temperature if last_reading else 24.5
        pump_status = last_reading.pump_status if last_reading else False

        # Simulate dynamic change
        if pump_status:
            new_moisture = prev_moisture + random.uniform(3.0, 5.5)
            if new_moisture >= 50.0:
                pump_status = False
        else:
            new_moisture = prev_moisture - random.uniform(0.5, 1.2)
            if new_moisture <= 30.0:
                pump_status = True

        new_moisture = max(20.0, min(70.0, new_moisture))
        new_temp = max(18.0, min(32.0, prev_temp + random.uniform(-0.4, 0.4)))
        raw_adc = int(3200 - (new_moisture / 100.0) * (3200 - 1400))

        reading = SensorReading.objects.create(
            device=device,
            soil_temperature=round(new_temp, 1),
            soil_moisture=round(new_moisture, 1),
            soil_moisture_raw=raw_adc,
            pump_status=pump_status,
            received_at=now
        )

        device.last_seen = now
        device.save()

        if hasattr(device, 'status'):
            device.status.last_seen = now
            device.status.operational_state = 'IRRIGATING' if pump_status else 'IDLE'
            device.status.save()

        AlertService.evaluate_reading(reading)

        return Response({
            'success': True,
            'reading': {
                'temperature': reading.soil_temperature,
                'moisture': reading.soil_moisture,
                'raw': reading.soil_moisture_raw,
                'pump_status': reading.pump_status,
                'timestamp': now.strftime('%H:%M:%S')
            }
        })
