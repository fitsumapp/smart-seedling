"""Admin interfaces for nursery entities using native Django Unfold features."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from .models import Nursery, NurseryZone, SeedlingBatch


class NurseryZoneInline(TabularInline):
    model = NurseryZone
    extra = 1

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_authenticated:
            return qs.none()
        if getattr(request.user, 'is_super_admin', False):
            return qs
        if getattr(request.user, 'assigned_nursery', None):
            return qs.filter(nursery=request.user.assigned_nursery)
        return qs.none()


@admin.register(Nursery)
class NurseryAdmin(ModelAdmin):
    list_display = ('nursery_header', 'location', 'is_active_badge', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('code', 'name', 'location')
    inlines = [NurseryZoneInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request).prefetch_related('zones')
        if not request.user.is_authenticated:
            return qs.none()
        if getattr(request.user, 'is_super_admin', False):
            return qs
        if getattr(request.user, 'assigned_nursery', None):
            return qs.filter(id=request.user.assigned_nursery_id)
        return qs.none()

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_nurseries', True)

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_nurseries', True)

    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        is_nursery = getattr(request.user, 'is_nursery_admin', False)
        return (is_nursery or is_super) and getattr(request.user, 'can_access_nurseries', True)

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        if not (is_super or getattr(request.user, 'can_access_nurseries', True)):
            return False
        if is_super:
            return True
        if obj is None:
            return getattr(request.user, 'is_nursery_admin', False)
        return request.user.can_manage_nursery(obj)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) and getattr(request.user, 'can_access_nurseries', True)

    @display(description=_('Nursery Facility'), header=True)
    def nursery_header(self, obj):
        return [
            obj.name,
            f"Code: {obj.code}"
        ]

    @display(description=_('Active Status'), boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active


@admin.register(NurseryZone)
class NurseryZoneAdmin(ModelAdmin):
    list_display = ('zone_header', 'nursery_display', 'is_active_badge', 'created_at')
    list_filter = ('nursery', 'is_active')
    search_fields = ('code', 'name', 'nursery__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('nursery')
        if not request.user.is_authenticated:
            return qs.none()
        if getattr(request.user, 'is_super_admin', False):
            return qs
        if getattr(request.user, 'assigned_nursery', None):
            return qs.filter(nursery=request.user.assigned_nursery)
        return qs.none()

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_zones', True)

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_zones', True)

    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        is_nursery = getattr(request.user, 'is_nursery_admin', False)
        return (is_nursery or is_super) and getattr(request.user, 'can_access_zones', True)

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        if not (is_super or getattr(request.user, 'can_access_zones', True)):
            return False
        if is_super:
            return True
        if obj is None:
            return getattr(request.user, 'is_nursery_admin', False)
        return request.user.can_manage_nursery(obj.nursery)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        if not (is_super or getattr(request.user, 'can_access_zones', True)):
            return False
        if is_super:
            return True
        if obj is None:
            return getattr(request.user, 'is_nursery_admin', False)
        return request.user.can_manage_nursery(obj.nursery)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_authenticated and not getattr(request.user, 'is_super_admin', False):
            if getattr(request.user, 'assigned_nursery', None):
                if db_field.name == "nursery":
                    kwargs["queryset"] = Nursery.objects.filter(id=request.user.assigned_nursery_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @display(description=_('Propagation Zone'), header=True)
    def zone_header(self, obj):
        return [
            obj.name,
            f"Code: {obj.code}"
        ]

    @display(description=_('Nursery Facility'))
    def nursery_display(self, obj):
        return obj.nursery.name

    @display(description=_('Active Status'), boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active


@admin.register(SeedlingBatch)
class SeedlingBatchAdmin(ModelAdmin):
    list_display = (
        'plant_header',
        'growth_stage_badge',
        'age_display',
        'quantity_display',
        'facility_display',
        'qr_code_thumbnail',
        'quick_actions'
    )
    list_filter = ('nursery', 'status', 'planting_date')
    search_fields = ('batch_code', 'plant_name', 'variety', 'species', 'qr_token')
    readonly_fields = ('qr_token', 'qr_code_large_preview', 'created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('nursery', 'nursery_zone')
        if not request.user.is_authenticated:
            return qs.none()
        if getattr(request.user, 'is_super_admin', False):
            return qs
        if getattr(request.user, 'assigned_nursery', None):
            return qs.filter(nursery=request.user.assigned_nursery)
        return qs.none()

    def has_module_permission(self, request):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_batches', True)

    def has_view_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, 'is_super_admin', False) or getattr(request.user, 'can_access_batches', True)

    def has_add_permission(self, request):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        is_nursery = getattr(request.user, 'is_nursery_admin', False)
        return (is_nursery or is_super) and getattr(request.user, 'can_access_batches', True)

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        if not (is_super or getattr(request.user, 'can_access_batches', True)):
            return False
        if is_super:
            return True
        if obj is None:
            return getattr(request.user, 'is_nursery_admin', False)
        return request.user.can_manage_nursery(obj.nursery)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_authenticated:
            return False
        is_super = getattr(request.user, 'is_super_admin', False)
        if not (is_super or getattr(request.user, 'can_access_batches', True)):
            return False
        if is_super:
            return True
        if obj is None:
            return getattr(request.user, 'is_nursery_admin', False)
        return request.user.can_manage_nursery(obj.nursery)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if request.user.is_authenticated and not getattr(request.user, 'is_super_admin', False):
            if getattr(request.user, 'assigned_nursery', None):
                if db_field.name == "nursery":
                    kwargs["queryset"] = Nursery.objects.filter(id=request.user.assigned_nursery_id)
                elif db_field.name == "nursery_zone":
                    kwargs["queryset"] = NurseryZone.objects.filter(nursery=request.user.assigned_nursery)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @display(description=_('Plant Profile'), header=True)
    def plant_header(self, obj):
        variety_info = f"Variety: {obj.variety}" if obj.variety else "Standard"
        return [
            obj.plant_name,
            f"Batch: {obj.batch_code} ({variety_info})"
        ]

    @display(description=_('Growth Stage'), label=True)
    def growth_stage_badge(self, obj):
        stage_colors = {
            'SEEDED': 'info',
            'GERMINATING': 'warning',
            'GROWING': 'success',
            'READY': 'success',
            'TRANSPLANTED': 'secondary',
            'FAILED': 'danger'
        }
        return obj.get_status_display(), stage_colors.get(obj.status, 'info')

    @display(description=_('Age'))
    def age_display(self, obj):
        return f"{obj.age_days} days"

    @display(description=_('Tray Qty'))
    def quantity_display(self, obj):
        return f"{obj.quantity:,} units"

    @display(description=_('Facility & Zone'))
    def facility_display(self, obj):
        zone_name = obj.nursery_zone.name if obj.nursery_zone else "General"
        return f"{obj.nursery.name} - {zone_name}"

    @display(description=_('QR Passport'))
    def qr_code_thumbnail(self, obj):
        return format_html(
            '<a href="/plant/{}/" target="_blank">'
            '<img src="/plant/{}/qr/" width="38" height="38" style="border-radius: 6px; border: 1px solid #d1d5db;" alt="QR" />'
            '</a>',
            obj.qr_token,
            obj.qr_token
        )

    @display(description=_('Quick Actions'))
    def quick_actions(self, obj):
        return format_html(
            '<a href="/plant/{}/" target="_blank" class="button" style="padding: 4px 8px; font-size: 11px; margin-right: 4px; background: #22c55e; color: #072714; font-weight: 700; border-radius: 4px; text-decoration: none;">'
            'Passport'
            '</a>'
            '<a href="/plant/{}/print/" target="_blank" class="button" style="padding: 4px 8px; font-size: 11px; background: #1e293b; color: white; border-radius: 4px; text-decoration: none;">'
            'Sticker'
            '</a>',
            obj.qr_token,
            obj.qr_token
        )

    def qr_code_large_preview(self, obj):
        if obj.pk:
            return format_html(
                '<div style="text-align: center; max-width: 260px; padding: 15px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;">'
                '<img src="/plant/{}/qr/" width="180" height="180" style="display: block; margin: 0 auto 10px; border-radius: 8px;" alt="QR Code" />'
                '<p style="font-size: 12px; color: #64748b; word-break: break-all; margin: 0;"><strong>Token:</strong> {}</p>'
                '<div style="margin-top: 10px;">'
                '<a href="/plant/{}/" target="_blank" class="button" style="margin-right: 5px; font-size: 12px;">View Passport</a>'
                '<a href="/plant/{}/print/" target="_blank" class="button" style="font-size: 12px;">Print Sticker</a>'
                '</div>'
                '</div>',
                obj.qr_token,
                obj.qr_token,
                obj.qr_token,
                obj.qr_token
            )
        return "-"

    qr_code_large_preview.short_description = _("QR Code Preview")
