"""Admin interfaces for alerts using native Django Unfold features."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from .models import Alert


@admin.register(Alert)
class AlertAdmin(ModelAdmin):
    list_display = (
        'alert_header',
        'severity_badge',
        'device_display',
        'is_resolved_badge',
        'created_at'
    )
    list_filter = ('alert_type', 'severity', 'is_resolved', 'device__nursery_zone__nursery')
    search_fields = ('message', 'device__device_id', 'device__name')
    readonly_fields = ('device', 'alert_type', 'severity', 'message', 'created_at', 'resolved_at')
    actions = ['mark_as_resolved']

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
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_alerts', True)

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_alerts', True)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        if not (is_super or getattr(request.user, 'can_access_alerts', True)):
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
        return getattr(request.user, 'is_super_admin', False)


    @display(description=_('Alert Message'), header=True)
    def alert_header(self, obj):
        return [
            obj.get_alert_type_display(),
            obj.message
        ]

    @display(description=_('Severity'), label=True)
    def severity_badge(self, obj):
        severity_colors = {
            'CRITICAL': 'danger',
            'WARNING': 'warning',
            'INFO': 'info',
        }
        return obj.severity, severity_colors.get(obj.severity, 'secondary')

    @display(description=_('Hardware Node'))
    def device_display(self, obj):
        return f"{obj.device.name} ({obj.device.device_id})"

    @display(description=_('Resolved'), boolean=True)
    def is_resolved_badge(self, obj):
        return obj.is_resolved

    @action(description=_("Mark selected alerts as resolved"))
    def mark_as_resolved(self, request, queryset):
        for alert in queryset:
            alert.resolve()
            alert.save()
        self.message_user(request, f"Successfully resolved {queryset.count()} alert(s).")
