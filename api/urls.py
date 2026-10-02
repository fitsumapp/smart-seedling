"""API URL Configuration."""

from django.urls import path
from api.views import (
    DeviceReadingIngestView,
    DeviceSettingsView,
    DeviceHeartbeatView
)

app_name = 'api'

urlpatterns = [
    path('v1/device/readings/', DeviceReadingIngestView.as_view(), name='device-readings'),
    path('v1/device/settings/', DeviceSettingsView.as_view(), name='device-settings'),
    path('v1/device/heartbeat/', DeviceHeartbeatView.as_view(), name='device-heartbeat'),
]
