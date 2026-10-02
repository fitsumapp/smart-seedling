"""REST API Views for ESP32 IoT interactions and telemetry ingest."""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from devices.models import Device
from devices.authentication import DeviceAuthentication
from monitoring.models import SensorReading
from alerts.services import AlertService
from api.serializers import (
    SensorReadingIngestSerializer,
    DeviceSettingsSerializer,
    DeviceHeartbeatSerializer
)
from api.throttling import DeviceRateThrottle


def get_client_ip(request) -> str:
    """Extract client IP safely from request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class DeviceBaseAPIView(APIView):
    """Base API view enforcing device authentication and rate throttling."""
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [DeviceRateThrottle]

    def get_authenticated_device(self, request) -> Device:
        if hasattr(request.user, 'device'):
            return request.user.device
        if isinstance(request.auth, Device):
            return request.auth
        return None


class DeviceReadingIngestView(DeviceBaseAPIView):
    """
    POST /api/v1/device/readings/
    Receives and processes real-time sensor telemetry from ESP32.
    """

    def post(self, request, *args, **kwargs):
        device = self.get_authenticated_device(request)
        if not device:
            return Response(
                {'success': False, 'error': 'Authentication failed or missing device context.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = SensorReadingIngestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        # Ensure device_id in payload matches authenticated device
        if data['device_id'] != device.device_id:
            return Response(
                {'success': False, 'error': 'device_id in payload does not match authenticated hardware credentials.'},
                status=status.HTTP_403_FORBIDDEN
            )

        now = timezone.now()
        client_ip = get_client_ip(request)

        # 1. Create and persist sensor reading
        reading = SensorReading.objects.create(
            device=device,
            soil_temperature=data['soil_temperature'],
            soil_moisture=data['soil_moisture'],
            soil_moisture_raw=data['soil_moisture_raw'],
            air_temperature=data.get('air_temperature'),
            air_humidity=data.get('air_humidity'),
            pump_status=data['pump_status'],
            fan_status=data.get('fan_status', False),
            device_timestamp=data.get('device_timestamp')
        )

        # 2. Update Device & DeviceStatus
        device.last_seen = now
        if data.get('firmware_version'):
            device.firmware_version = data['firmware_version']
        device.save(update_fields=['last_seen', 'firmware_version', 'updated_at'])

        if hasattr(device, 'status'):
            device_status = device.status
            device_status.last_seen = now
            device_status.last_ip = client_ip
            if data.get('rssi') is not None:
                device_status.rssi = data['rssi']
            if data.get('firmware_version'):
                device_status.firmware_version = data['firmware_version']
            
            p_on = data['pump_status']
            f_on = data.get('fan_status', False)
            if p_on and f_on:
                device_status.operational_state = 'IRRIGATING & COOLING'
            elif p_on:
                device_status.operational_state = 'IRRIGATING'
            elif f_on:
                device_status.operational_state = 'COOLING / VENTILATING'
            else:
                device_status.operational_state = 'IDLE'
            device_status.save()

        # 3. Evaluate alerts asynchronously or immediately via service layer
        AlertService.evaluate_reading(reading)

        # Prepare active settings for instant on-the-fly threshold synchronization
        settings_dict = {}
        if hasattr(device, 'settings'):
            s = device.settings
            settings_dict = {
                'pump_on_threshold': s.pump_on_threshold,
                'pump_off_threshold': s.pump_off_threshold,
                'fan_on_temperature': s.fan_on_temperature,
                'fan_off_temperature': s.fan_off_temperature,
                'fan_on_humidity': s.fan_on_humidity,
                'reading_interval_seconds': s.reading_interval_seconds,
                'upload_interval_seconds': s.upload_interval_seconds,
                'automatic_mode': s.automatic_mode,
                'max_pump_runtime_seconds': s.max_pump_runtime_seconds,
            }

        return Response(
            {
                'success': True,
                'message': 'reading_saved',
                'server_time': now.isoformat(),
                'settings': settings_dict
            },
            status=status.HTTP_201_CREATED
        )


class DeviceSettingsView(DeviceBaseAPIView):
    """
    GET /api/v1/device/settings/
    Returns current irrigation thresholds and operational intervals for the ESP32.
    """

    def get(self, request, *args, **kwargs):
        device = self.get_authenticated_device(request)
        if not device:
            return Response(
                {'success': False, 'error': 'Authentication failed.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            settings_obj = device.settings
        except Exception:
            return Response(
                {'success': False, 'error': 'Device settings not configured.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = DeviceSettingsSerializer(settings_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeviceHeartbeatView(DeviceBaseAPIView):
    """
    POST /api/v1/device/heartbeat/
    Periodic lightweight keep-alive ping from ESP32 to maintain online status and signal health.
    """

    def post(self, request, *args, **kwargs):
        device = self.get_authenticated_device(request)
        if not device:
            return Response(
                {'success': False, 'error': 'Authentication failed.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = DeviceHeartbeatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        now = timezone.now()
        client_ip = get_client_ip(request)

        # Update last seen and status
        device.last_seen = now
        if data.get('firmware_version'):
            device.firmware_version = data['firmware_version']
        device.save(update_fields=['last_seen', 'firmware_version', 'updated_at'])

        if hasattr(device, 'status'):
            device_status = device.status
            device_status.last_seen = now
            device_status.last_ip = client_ip
            if data.get('rssi') is not None:
                device_status.rssi = data['rssi']
            if data.get('firmware_version'):
                device_status.firmware_version = data['firmware_version']
            if data.get('operational_state'):
                device_status.operational_state = data['operational_state']
            device_status.save()

        return Response(
            {
                'success': True,
                'message': 'heartbeat_acknowledged',
                'server_time': now.isoformat()
            },
            status=status.HTTP_200_OK
        )
