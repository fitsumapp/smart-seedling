"""Nursery app configuration."""
from django.apps import AppConfig


class NurseryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nursery'
    verbose_name = 'Nurseries & Seedling Management'
