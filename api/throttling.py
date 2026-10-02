"""Throttling classes for IoT telemetry and rate-limiting."""

from rest_framework.throttling import SimpleRateThrottle


class DeviceRateThrottle(SimpleRateThrottle):
    """
    Limits requests based on the authenticated ESP32 Device ID.
    Falls back to client IP if unauthenticated.
    """
    scope = 'device'

    def get_cache_key(self, request, view):
        if hasattr(request, 'user') and getattr(request.user, 'is_device', False):
            ident = request.user.device.device_id
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
