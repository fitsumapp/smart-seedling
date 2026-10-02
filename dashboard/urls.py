"""Dashboard URL Routing."""

from django.urls import path
from dashboard.views import (
    DashboardView,
    DashboardTelemetryAPIView,
    DashboardSimulateAPIView
)

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('dashboard/', DashboardView.as_view(), name='dashboard-page'),
    path('api/telemetry/', DashboardTelemetryAPIView.as_view(), name='api-telemetry'),
    path('dashboard/api/telemetry/', DashboardTelemetryAPIView.as_view(), name='dashboard-api-telemetry'),
    path('api/simulate/', DashboardSimulateAPIView.as_view(), name='api-simulate'),
    path('dashboard/api/simulate/', DashboardSimulateAPIView.as_view(), name='dashboard-api-simulate'),
]
