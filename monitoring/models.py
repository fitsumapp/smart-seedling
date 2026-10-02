"""Telemetry models for IoT sensor readings."""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class SensorReading(models.Model):
    """Time-series telemetry reading emitted by an ESP32 device."""
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='readings',
        help_text=_('Originating ESP32 device.')
    )
    soil_temperature = models.FloatField(
        validators=[MinValueValidator(-20.0), MaxValueValidator(80.0)],
        help_text=_('Soil temperature in degrees Celsius (DS18B20).')
    )
    soil_moisture = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Calibrated soil moisture percentage (0-100%).')
    )
    soil_moisture_raw = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4095)],
        help_text=_('Raw 12-bit ADC reading from capacitive sensor (0-4095).')
    )
    air_temperature = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-40.0), MaxValueValidator(80.0)],
        help_text=_('Ambient air temperature in degrees Celsius (DHT22).')
    )
    air_humidity = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Ambient air relative humidity percentage (DHT22).')
    )
    pump_status = models.BooleanField(
        help_text=_('Actuation state of the 5V water pump relay (True=ON, False=OFF).')
    )
    fan_status = models.BooleanField(
        default=False,
        help_text=_('Actuation state of the ventilation/cooling fan relay (True=ON, False=OFF).')
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Timestamp recorded by the backend server.')
    )
    device_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Optional timestamp sent directly by device RTC.')
    )

    class Meta:
        ordering = ['-received_at']
        verbose_name = _('Sensor Reading')
        verbose_name_plural = _('Sensor Readings')
        indexes = [
            models.Index(fields=['device', 'received_at'], name='sensor_dev_received_idx'),
            models.Index(fields=['-received_at'], name='sensor_received_desc_idx'),
        ]

    def __str__(self):
        pump_str = "PUMP ON" if self.pump_status else "PUMP OFF"
        return f"[{self.received_at.strftime('%Y-%m-%d %H:%M:%S')}] {self.device.device_id}: {self.soil_temperature:.1f}°C, {self.soil_moisture:.1f}% ({pump_str})"
