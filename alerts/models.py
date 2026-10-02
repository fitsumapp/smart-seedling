"""Alert models for operational threshold and system exception tracking."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class AlertType(models.TextChoices):
    LOW_SOIL_MOISTURE = 'LOW_SOIL_MOISTURE', _('Low Soil Moisture')
    HIGH_SOIL_TEMPERATURE = 'HIGH_SOIL_TEMPERATURE', _('High Soil Temperature')
    DEVICE_OFFLINE = 'DEVICE_OFFLINE', _('Device Offline')
    SENSOR_ERROR = 'SENSOR_ERROR', _('Sensor Reading Error')
    PUMP_TIMEOUT = 'PUMP_TIMEOUT', _('Pump Safety Timeout')


class AlertSeverity(models.TextChoices):
    INFO = 'INFO', _('Info')
    WARNING = 'WARNING', _('Warning')
    CRITICAL = 'CRITICAL', _('Critical')


class Alert(models.Model):
    """Stores system alerts for abnormal conditions or device failures."""
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    alert_type = models.CharField(
        max_length=40,
        choices=AlertType.choices,
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=AlertSeverity.choices,
        default=AlertSeverity.WARNING,
        db_index=True
    )
    message = models.TextField()
    is_resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Alert')
        verbose_name_plural = _('Alerts')
        indexes = [
            models.Index(fields=['device', 'is_resolved', 'alert_type'], name='alert_dev_status_type_idx'),
        ]

    def __str__(self):
        status = "RESOLVED" if self.is_resolved else "ACTIVE"
        return f"[{self.severity}] {self.get_alert_type_display()} - {self.device.device_id} ({status})"

    def resolve(self):
        """Marks alert as resolved."""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save(update_fields=['is_resolved', 'resolved_at'])
