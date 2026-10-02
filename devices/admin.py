"""Admin interfaces for devices and irrigation settings using native Django Unfold decorators."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from .models import Device, DeviceSetting, DeviceStatus


class DeviceSettingInline(TabularInline):
    model = DeviceSetting
    can_delete = False
    extra = 0
    fields = (
        'pump_on_threshold',
        'pump_off_threshold',
        'fan_on_temperature',
        'fan_off_temperature',
        'fan_on_humidity',
        'reading_interval_seconds',
        'upload_interval_seconds',
        'automatic_mode'
    )


class DeviceStatusInline(TabularInline):
    model = DeviceStatus
    can_delete = False
    extra = 0
    readonly_fields = ('last_seen', 'rssi', 'last_ip', 'firmware_version', 'operational_state')


@admin.register(Device)
class DeviceAdmin(ModelAdmin):
    list_display = (
        'device_header',
        'nursery_zone_display',
        'connection_badge',
        'firmware_version',
        'last_seen',
    )
    list_filter = ('is_active', 'firmware_version', 'nursery_zone__nursery')
    search_fields = ('device_id', 'name', 'nursery_zone__name')
    readonly_fields = ('device_id', 'api_key_hash', 'api_key_prefix', 'last_seen', 'created_at', 'updated_at')
    inlines = [DeviceSettingInline, DeviceStatusInline]
    actions = ['regenerate_api_keys']

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('nursery_zone__nursery', 'status', 'settings')
        if not request.user.is_authenticated:
            return qs.none()
        if getattr(request.user, 'is_super_admin', False):
            return qs
        if getattr(request.user, 'assigned_nursery', None):
            return qs.filter(nursery_zone__nursery=request.user.assigned_nursery)
        return qs.none()

    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False)

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        if getattr(request.user, 'is_super_admin', False):
            return True
        if obj is None:
            return getattr(request.user, 'is_nursery_admin', False)
        if obj.nursery_zone and obj.nursery_zone.nursery:
            return request.user.can_manage_nursery(obj.nursery_zone.nursery)
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False)

    @display(description=_('Device Node'), header=True)
    def device_header(self, obj):
        return [
            obj.name,
            f"ID: {obj.device_id}"
        ]

    @display(description=_('Nursery Zone'))
    def nursery_zone_display(self, obj):
        if obj.nursery_zone:
            return f"{obj.nursery_zone.name} ({obj.nursery_zone.nursery.code})"
        return "-"

    @display(description=_('Connection Status'), label=True)
    def connection_badge(self, obj):
        if obj.is_online:
            rssi = obj.status.rssi if hasattr(obj, 'status') and obj.status.rssi else -58
            return "ONLINE", "success"
        return "OFFLINE", "danger"

    @action(description=_("Regenerate API Key for selected devices"))
    def regenerate_api_keys(self, request, queryset):
        for device in queryset:
            device.regenerate_api_key()
        self.message_user(request, f"Successfully regenerated API keys for {queryset.count()} device(s).")


@admin.register(DeviceSetting)
class DeviceSettingAdmin(ModelAdmin):
    list_display = (
        'device_header',
        'irrigation_thresholds_display',
        'ventilation_thresholds_display',
        'intervals_display',
        'automatic_mode_badge',
        'safety_cutoff',
        'updated_at'
    )
    search_fields = ('device__device_id', 'device__name')
    fieldsets = (
        (_('Target IoT Hardware Node'), {
            'fields': ('device', 'automatic_mode'),
            'description': _('Assign threshold configurations to the IoT controller hardware unit.')
        }),
        (_('💧 Soil Moisture & Irrigation Pump Control'), {
            'fields': (
                ('pump_on_threshold', 'pump_off_threshold'),
                'max_pump_runtime_seconds',
            ),
            'description': _('Control automated irrigation. Pump starts when soil moisture drops to ON threshold and stops at OFF threshold.')
        }),
        (_('💨 Ambient Air Temperature & Ventilation Fan Control (DHT22)'), {
            'fields': (
                ('fan_on_temperature', 'fan_off_temperature'),
                'fan_on_humidity',
            ),
            'description': _('Control automated greenhouse cooling fan. Fan starts when air temperature reaches or exceeds ON threshold and stops when cooled to OFF threshold.')
        }),
        (_('⏱️ Telemetry Sampling & Cloud Upload Intervals'), {
            'fields': (
                ('reading_interval_seconds', 'upload_interval_seconds'),
            ),
            'classes': ('collapse',),
        }),
    )

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
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_irrigation', True)

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_irrigation', True)

    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        is_nursery = getattr(request.user, 'is_nursery_admin', False)
        return (is_nursery or is_super) and getattr(request.user, 'can_access_irrigation', True)

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        if not (is_super or getattr(request.user, 'can_access_irrigation', True)):
            return False
        if is_super:
            return True
        if obj is None:
            return getattr(request.user, 'is_nursery_admin', False)
        if obj.device and obj.device.nursery_zone and obj.device.nursery_zone.nursery:
            return request.user.can_manage_nursery(obj.device.nursery_zone.nursery)
        return False

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) and getattr(request.user, 'can_access_irrigation', True)

    @display(description=_('Device Node'), header=True)
    def device_header(self, obj):
        return [
            obj.device.name,
            f"Hardware ID: {obj.device.device_id}"
        ]

    @display(description=_('Irrigation Band (Pump ON / OFF)'))
    def irrigation_thresholds_display(self, obj):
        return f"💧 ON ≤ {obj.pump_on_threshold}% → OFF ≥ {obj.pump_off_threshold}%"

    @display(description=_('Ventilation Band (Fan ON / OFF)'))
    def ventilation_thresholds_display(self, obj):
        return f"💨 ON ≥ {obj.fan_on_temperature}°C → OFF ≤ {obj.fan_off_temperature}°C | Hum ≥ {obj.fan_on_humidity}%"

    @display(description=_('Sampling / Sync'))
    def intervals_display(self, obj):
        return f"Sampling: {obj.reading_interval_seconds}s | Upload: {obj.upload_interval_seconds}s"

    @display(description=_('Automatic Mode'), boolean=True)
    def automatic_mode_badge(self, obj):
        return obj.automatic_mode

    @display(description=_('Safety Timeout'))
    def safety_cutoff(self, obj):
        return f"Max {obj.max_pump_runtime_seconds}s"
