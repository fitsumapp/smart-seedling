"""Models for ESP32 devices, settings, and hardware statuses."""

import secrets
import hashlib
from datetime import timedelta
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hex digest of a raw API key token."""
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


class Device(models.Model):
    """Represents an ESP32 IoT monitoring and pump control device."""
    nursery_zone = models.ForeignKey(
        'nursery.NurseryZone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devices',
        help_text=_('Nursery zone where this hardware unit is deployed.')
    )
    device_id = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_('Hardware identifier, e.g. ESP32-001 or MAC address based ID.')
    )
    name = models.CharField(max_length=100, help_text=_('Human-readable nickname for the unit.'))
    api_key_hash = models.CharField(max_length=128, editable=False)
    api_key_prefix = models.CharField(max_length=16, editable=False, db_index=True)
    firmware_version = models.CharField(max_length=30, default='1.0.0')
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['device_id']
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')

    def __str__(self):
        zone_info = f" ({self.nursery_zone})" if self.nursery_zone else ""
        return f"{self.device_id} - {self.name}{zone_info}"

    def set_api_key(self, raw_token: str = None) -> str:
        """Sets new hashed API key and returns raw token for one-time display."""
        if not raw_token:
            raw_token = secrets.token_urlsafe(32)
        self.api_key_prefix = raw_token[:8]
        self.api_key_hash = hash_token(raw_token)
        return raw_token

    def verify_api_key(self, raw_token: str) -> bool:
        """Verifies if given token matches stored hash in constant time."""
        if not self.api_key_hash or not raw_token:
            return False
        return secrets.compare_digest(self.api_key_hash, hash_token(raw_token))

    @property
    def is_online(self) -> bool:
        """Calculates online status dynamically based on upload interval + grace threshold."""
        if not self.last_seen or not self.is_active:
            return False
        try:
            upload_interval = self.settings.upload_interval_seconds
        except Exception:
            upload_interval = 10
        # Allow 3x upload interval plus 15s grace period
        timeout_seconds = max(upload_interval * 3, 30) + 15
        return timezone.now() - self.last_seen <= timedelta(seconds=timeout_seconds)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        raw_key = None
        if not self.api_key_hash:
            raw_key = self.set_api_key()

        self.device_id = self.device_id.strip()
        super().save(*args, **kwargs)

        # Auto-create settings and status if not present
        if is_new or not hasattr(self, 'settings'):
            DeviceSetting.objects.get_or_create(device=self)
        if is_new or not hasattr(self, 'status'):
            DeviceStatus.objects.get_or_create(device=self)

        return raw_key


class DeviceSetting(models.Model):
    """Operating thresholds and intervals synchronised with the ESP32."""
    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    pump_on_threshold = models.FloatField(
        default=30.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Soil moisture percentage below which irrigation turns ON.')
    )
    pump_off_threshold = models.FloatField(
        default=50.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Soil moisture percentage above which irrigation turns OFF.')
    )
    fan_on_temperature = models.FloatField(
        default=30.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(80.0)],
        help_text=_('Air temperature (°C) above which ventilation fan turns ON.')
    )
    fan_off_temperature = models.FloatField(
        default=25.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(80.0)],
        help_text=_('Air temperature (°C) below which ventilation fan turns OFF.')
    )
    fan_on_humidity = models.FloatField(
        default=85.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Air relative humidity (%) above which ventilation fan turns ON.')
    )
    reading_interval_seconds = models.PositiveIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(3600)],
        help_text=_('Sensor sampling period in seconds.')
    )
    upload_interval_seconds = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(3600)],
        help_text=_('Telemetry upload period to server in seconds.')
    )
    automatic_mode = models.BooleanField(
        default=True,
        help_text=_('Enable autonomous local threshold-based relay actuation on ESP32/ESP8266.')
    )
    max_pump_runtime_seconds = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(600)],
        help_text=_('Maximum continuous pump runtime to prevent flood/dry-run.')
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Device Setting')
        verbose_name_plural = _('Device Settings')

    def __str__(self):
        return f"Settings for {self.device.device_id} (Pump: {self.pump_on_threshold}%-{self.pump_off_threshold}%, Fan: {self.fan_on_temperature}°C)"

    def clean(self):
        super().clean()
        if self.pump_on_threshold is not None and self.pump_off_threshold is not None:
            if self.pump_off_threshold <= self.pump_on_threshold:
                raise ValidationError({
                    'pump_off_threshold': _('Pump OFF threshold must be strictly greater than Pump ON threshold.')
                })
        if self.fan_on_temperature is not None and self.fan_off_temperature is not None:
            if self.fan_off_temperature >= self.fan_on_temperature:
                raise ValidationError({
                    'fan_off_temperature': _('Fan OFF temperature must be strictly less than Fan ON temperature.')
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DeviceStatus(models.Model):
    """Latest health and network status for an ESP32 unit."""
    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        related_name='status'
    )
    rssi = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Wi-Fi Signal strength in dBm (e.g. -65).')
    )
    firmware_version = models.CharField(max_length=30, blank=True)
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    operational_state = models.CharField(max_length=50, default='IDLE')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Device Status')
        verbose_name_plural = _('Device Statuses')

    def __str__(self):
        online_str = "ONLINE" if self.device.is_online else "OFFLINE"
        return f"Status for {self.device.device_id} [{online_str}]"
