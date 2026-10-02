"""Admin interfaces for sensor readings using native Django Unfold features."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import SensorReading


@admin.register(SensorReading)
class SensorReadingAdmin(ModelAdmin):
    list_display = (
        'device_header',
        'moisture_display',
        'temp_display',
        'pump_status_badge',
        'received_at'
    )
    list_filter = ('pump_status', 'received_at', 'device__nursery_zone__nursery')
    search_fields = ('device__device_id', 'device__name')
    readonly_fields = ('device', 'soil_temperature', 'soil_moisture', 'soil_moisture_raw', 'pump_status', 'received_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('device__nursery_zone__nursery')
        if not request.user.is_authenticated:
            return qs.none()
        if getattr(request.user, 'is_super_admin', False):
            return qs
        if getattr(request.user, 'assigned_nursery', None):
            return qs.filter(device__nursery_zone__nursery=request.user.assigned_nursery)
        return qs.none()

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_telemetry', True)

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_telemetry', True)

    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        is_nursery = getattr(request.user, 'is_nursery_admin', False)
        return (is_nursery or is_super) and getattr(request.user, 'can_access_telemetry', True)

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        is_nursery = getattr(request.user, 'is_nursery_admin', False)
        return (is_nursery or is_super) and getattr(request.user, 'can_access_telemetry', True)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False)


    @display(description=_('IoT Node'), header=True)
    def device_header(self, obj):
        return [
            obj.device.name,
            f"Node ID: {obj.device.device_id}"
        ]

    @display(description=_('Soil Moisture'))
    def moisture_display(self, obj):
        return f"{obj.soil_moisture:.1f}% (ADC: {obj.soil_moisture_raw})"

    @display(description=_('Soil Temperature'))
    def temp_display(self, obj):
        return f"{obj.soil_temperature:.1f}°C"

    @display(description=_('Pump State'), label=True)
    def pump_status_badge(self, obj):
        if obj.pump_status:
            return "IRRIGATING", "success"
        return "IDLE (OFF)", "secondary"
