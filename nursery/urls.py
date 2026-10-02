"""Nursery and Plant QR Code URL Routing."""

from django.urls import path
from nursery.views import (
    SeedlingPublicDetailView,
    SeedlingQRCodeImageView,
    SeedlingPrintLabelView
)

app_name = 'nursery'

urlpatterns = [
    path('plant/<str:qr_token>/', SeedlingPublicDetailView.as_view(), name='public-plant-detail'),
    path('plant/<str:qr_token>/qr.png', SeedlingQRCodeImageView.as_view(), name='plant-qr-image'),
    path('plant/<str:qr_token>/label/', SeedlingPrintLabelView.as_view(), name='plant-print-label'),
]
