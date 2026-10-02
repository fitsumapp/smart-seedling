"""Accounts and User Management Models."""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')
    NURSERY_ADMIN = 'NURSERY_ADMIN', _('Nursery Administrator')
    OPERATOR = 'OPERATOR', _('Operator')


class User(AbstractUser):
    """Custom User model with role-based access control."""
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.OPERATOR,
        help_text=_('Designates role and permission tier in the Smart Seedling system.')
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text=_('Contact phone number for operational alerts.')
    )
    assigned_nursery = models.ForeignKey(
        'nursery.Nursery',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_users',
        help_text=_('Primary nursery assigned for Nursery Administrators and Operators.')
    )

    # Granular Feature Access Toggles (Sidebar & Module Permissions)
    can_access_dashboard = models.BooleanField(
        default=True,
        verbose_name=_('Live Interactive Dashboard'),
        help_text=_('Enable to display and grant access to the Live Interactive Dashboard.')
    )
    can_access_telemetry = models.BooleanField(
        default=True,
        verbose_name=_('Sensor Telemetry Readings'),
        help_text=_('Enable to display and grant access to Sensor Telemetry Readings.')
    )
    can_access_alerts = models.BooleanField(
        default=True,
        verbose_name=_('System Alerts & Warnings'),
        help_text=_('Enable to display and grant access to System Alerts & Warnings.')
    )
    can_access_nurseries = models.BooleanField(
        default=True,
        verbose_name=_('Nurseries'),
        help_text=_('Enable to display and grant access to Nurseries management.')
    )
    can_access_zones = models.BooleanField(
        default=True,
        verbose_name=_('Nursery Zones'),
        help_text=_('Enable to display and grant access to Nursery Zones management.')
    )
    can_access_irrigation = models.BooleanField(
        default=True,
        verbose_name=_('Irrigation Settings'),
        help_text=_('Enable to display and grant access to Irrigation Settings.')
    )
    can_access_batches = models.BooleanField(
        default=True,
        verbose_name=_('Seedling Batches'),
        help_text=_('Enable to display and grant access to Seedling Batches & QR Passports.')
    )

    class Meta:
        ordering = ['username']

        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        role_label = self.get_role_display()
        return f"{self.username} ({role_label})"

    @property
    def is_super_admin(self) -> bool:
        return self.is_superuser or self.role == UserRole.SUPER_ADMIN

    @property
    def is_nursery_admin(self) -> bool:
        return self.is_super_admin or self.role == UserRole.NURSERY_ADMIN

    @property
    def is_operator(self) -> bool:
        return self.is_super_admin or self.is_nursery_admin or self.role == UserRole.OPERATOR

    def can_manage_nursery(self, nursery) -> bool:
        """Check if user has permission to manage a specific nursery."""
        if self.is_super_admin:
            return True
        if self.role == UserRole.NURSERY_ADMIN and self.assigned_nursery_id == (nursery.id if hasattr(nursery, 'id') else nursery):
            return True
        return False


class ActivityLog(models.Model):
    """Audit log for critical administrative and operational actions."""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=100, db_index=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Activity Log')
        verbose_name_plural = _('Activity Logs')

    def __str__(self):
        actor = self.user.username if self.user else 'System/Device'
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {actor} - {self.action}"

    @classmethod
    def log(cls, action: str, user=None, details: dict = None, ip_address: str = None):
        """Helper to create an activity log entry safely."""
        return cls.objects.create(
            action=action,
            user=user if user and user.is_authenticated else None,
            details=details or {},
            ip_address=ip_address
        )
