"""Service layer for evaluating sensor readings and generating deduplicated alerts."""

import logging
from django.utils import timezone
from .models import Alert, AlertType, AlertSeverity

logger = logging.getLogger(__name__)


class AlertService:
    """Evaluates telemetry conditions and raises or resolves alerts intelligently."""

    @classmethod
    def evaluate_reading(cls, reading) -> list[Alert]:
        """
        Evaluates a newly received SensorReading against device settings and safety limits.
        Avoids creating duplicate open alerts.
        """
        device = reading.device
        created_alerts = []

        try:
            settings = device.settings
        except Exception:
            settings = None

        pump_on_threshold = settings.pump_on_threshold if settings else 30.0

        # 1. Low Soil Moisture Check
        if reading.soil_moisture < pump_on_threshold:
            severity = AlertSeverity.CRITICAL if reading.soil_moisture < (pump_on_threshold * 0.6) else AlertSeverity.WARNING
            msg = f"Soil moisture on {device.device_id} is {reading.soil_moisture:.1f}%, below target threshold of {pump_on_threshold:.1f}%."
            alert = cls._get_or_create_alert(
                device=device,
                alert_type=AlertType.LOW_SOIL_MOISTURE,
                severity=severity,
                message=msg
            )
            if alert:
                created_alerts.append(alert)
        else:
            # If moisture is now healthy, auto-resolve any open LOW_SOIL_MOISTURE alerts for this device
            cls._auto_resolve_alerts(device, AlertType.LOW_SOIL_MOISTURE)

        # 2. High Soil Temperature Check
        HIGH_TEMP_LIMIT = 38.0
        if reading.soil_temperature > HIGH_TEMP_LIMIT:
            msg = f"Soil temperature on {device.device_id} reached {reading.soil_temperature:.1f}°C, exceeding safety limit of {HIGH_TEMP_LIMIT}°C."
            alert = cls._get_or_create_alert(
                device=device,
                alert_type=AlertType.HIGH_SOIL_TEMPERATURE,
                severity=AlertSeverity.WARNING,
                message=msg
            )
            if alert:
                created_alerts.append(alert)
        else:
            cls._auto_resolve_alerts(device, AlertType.HIGH_SOIL_TEMPERATURE)

        # 3. Sensor Error Check (e.g. DS18B20 disconnected returns -127°C or 85°C, or invalid raw values)
        if reading.soil_temperature in (-127.0, 85.0) or reading.soil_moisture_raw == 0:
            msg = f"Sensor reporting abnormal error value on {device.device_id} (Temp: {reading.soil_temperature}°C, Raw ADC: {reading.soil_moisture_raw}). Check wiring."
            alert = cls._get_or_create_alert(
                device=device,
                alert_type=AlertType.SENSOR_ERROR,
                severity=AlertSeverity.CRITICAL,
                message=msg
            )
            if alert:
                created_alerts.append(alert)
        else:
            cls._auto_resolve_alerts(device, AlertType.SENSOR_ERROR)

        return created_alerts

    @classmethod
    def _get_or_create_alert(cls, device, alert_type: str, severity: str, message: str):
        """Creates an alert only if an active (unresolved) alert of this type doesn't already exist."""
        existing = Alert.objects.filter(
            device=device,
            alert_type=alert_type,
            is_resolved=False
        ).first()

        if existing:
            # Update message / severity if escalated, but do not create duplicate
            if existing.severity != severity or existing.message != message:
                existing.severity = severity
                existing.message = message
                existing.save(update_fields=['severity', 'message'])
            return None

        # Create new alert
        return Alert.objects.create(
            device=device,
            alert_type=alert_type,
            severity=severity,
            message=message,
            is_resolved=False
        )

    @classmethod
    def _auto_resolve_alerts(cls, device, alert_type: str):
        """Auto-resolves open alerts of a given type when normal conditions resume."""
        open_alerts = Alert.objects.filter(
            device=device,
            alert_type=alert_type,
            is_resolved=False
        )
        if open_alerts.exists():
            now = timezone.now()
            open_alerts.update(is_resolved=True, resolved_at=now)
