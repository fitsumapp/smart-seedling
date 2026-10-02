"""Custom Device API Key Authentication for ESP32 endpoints."""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from devices.models import Device


class DevicePrincipal:
    """Represents an authenticated ESP32 Device as an auth principal."""
    is_authenticated = True
    is_device = True
    is_superuser = False
    is_staff = False

    def __init__(self, device: Device):
        self.device = device
        self.username = f"device_{device.device_id}"
        self.id = device.id

    def __str__(self):
        return f"Authenticated Device: {self.device.device_id}"


class DeviceAuthentication(BaseAuthentication):
    """
    Authenticates ESP32 hardware using:
    - Headers: `X-Device-ID` and `X-API-Key`
    - Or Authorization header: `DeviceKey <device_id>:<api_key>` or `Bearer <api_key>`
    """

    def authenticate(self, request):
        device_id = request.headers.get('X-Device-ID') or request.META.get('HTTP_X_DEVICE_ID')
        api_key = request.headers.get('X-API-Key') or request.META.get('HTTP_X_API_KEY')

        # Check Authorization header format
        auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
        if auth_header and not (device_id and api_key):
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'devicekey':
                try:
                    dev_part, key_part = parts[1].split(':', 1)
                    device_id = dev_part.strip()
                    api_key = key_part.strip()
                except ValueError:
                    pass

        # If no device authentication headers present, let other auth schemes handle or fail
        if not device_id or not api_key:
            # Fallback: check if device_id is in request body (for POST requests) if api_key header exists
            if not device_id and hasattr(request, 'data') and isinstance(request.data, dict):
                device_id = request.data.get('device_id')

            if not device_id or not api_key:
                return None

        device_id = str(device_id).strip()
        api_key = str(api_key).strip()

        try:
            device = Device.objects.select_related('settings', 'status').get(device_id=device_id)
        except Device.DoesNotExist:
            raise AuthenticationFailed(_('Unknown device identifier.'))

        if not device.is_active:
            raise AuthenticationFailed(_('Device account is deactivated.'))

        if not device.verify_api_key(api_key):
            raise AuthenticationFailed(_('Invalid device API key.'))

        # Return tuple of (principal, device)
        principal = DevicePrincipal(device)
        return (principal, device)

    def authenticate_header(self, request):
        return 'DeviceKey'
