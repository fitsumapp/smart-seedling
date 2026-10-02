"""Serializers for ESP32 device communication and telemetry."""

from rest_framework import serializers
from monitoring.models import SensorReading
from devices.models import DeviceSetting


class SensorReadingIngestSerializer(serializers.Serializer):
    """Validates raw sensor telemetry uploaded by the ESP32."""
    device_id = serializers.CharField(
        max_length=64,
        required=True,
        help_text="ESP32 hardware device identifier matching the authenticated unit."
    )
    soil_temperature = serializers.FloatField(
        min_value=-20.0,
        max_value=80.0,
        required=True,
        help_text="Soil temperature in degrees Celsius."
    )
    soil_moisture = serializers.FloatField(
        min_value=0.0,
        max_value=100.0,
        required=True,
        help_text="Calibrated moisture percentage (0-100%)."
    )
    soil_moisture_raw = serializers.IntegerField(
        min_value=0,
        max_value=4095,
        required=True,
        help_text="Raw 12-bit analog reading from sensor (0-4095)."
    )
    air_temperature = serializers.FloatField(
        min_value=-40.0,
        max_value=80.0,
        required=False,
        allow_null=True,
        help_text="Ambient air temperature in degrees Celsius (DHT22)."
    )
    air_humidity = serializers.FloatField(
        min_value=0.0,
        max_value=100.0,
        required=False,
        allow_null=True,
        help_text="Ambient air relative humidity percentage (DHT22)."
    )
    pump_status = serializers.BooleanField(
        required=True,
        help_text="Current pump relay state (true = ON, false = OFF)."
    )
    fan_status = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Current fan relay state (true = ON, false = OFF)."
    )
    rssi = serializers.IntegerField(
        min_value=-120,
        max_value=0,
        required=False,
        allow_null=True,
        help_text="Wi-Fi signal strength in dBm."
    )
    firmware_version = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True,
        help_text="Running ESP32/ESP8266 firmware build."
    )
    device_timestamp = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Device-local RTC timestamp if available."
    )


class DeviceSettingsSerializer(serializers.ModelSerializer):
    """Outputs irrigation, cooling, and polling configuration consumed by ESP."""
    class Meta:
        model = DeviceSetting
        fields = [
            'pump_on_threshold',
            'pump_off_threshold',
            'fan_on_temperature',
            'fan_off_temperature',
            'fan_on_humidity',
            'reading_interval_seconds',
            'upload_interval_seconds',
            'automatic_mode',
            'max_pump_runtime_seconds',
        ]


class DeviceHeartbeatSerializer(serializers.Serializer):
    """Validates lightweight heartbeat ping from ESP32."""
    rssi = serializers.IntegerField(
        min_value=-120,
        max_value=0,
        required=False,
        allow_null=True
    )
    firmware_version = serializers.CharField(
        max_length=30,
        required=False,
        allow_blank=True
    )
    operational_state = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True
    )
