"""Admin interface for accounts and activity logging with Django Unfold."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from .models import User, ActivityLog


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Smart Seedling Role & Facility'), {'fields': ('role', 'assigned_nursery')}),
        (
            _('Sidebar Features & Module Permissions (ON / OFF)'),
            {
                'description': _('Toggle ON to display in the user sidebar and grant access, or toggle OFF to completely hide and restrict the feature.'),
                'fields': (
                    'can_access_dashboard',
                    'can_access_telemetry',
                    'can_access_alerts',
                    'can_access_nurseries',
                    'can_access_zones',
                    'can_access_irrigation',
                    'can_access_batches',
                ),
            }
        ),
        (_('Account Status & Super Admin Flags'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'assigned_nursery', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff', 'assigned_nursery')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')



@admin.register(ActivityLog)
class ActivityLogAdmin(ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('action', 'user__username', 'ip_address', 'details')
    readonly_fields = ('created_at', 'user', 'action', 'details', 'ip_address')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

