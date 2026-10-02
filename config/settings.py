"""
Django settings for smart_seedling project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
from django.templatetags.static import static

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-smart-seedling-dev-fallback-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't', 'yes')

ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', 'seedling.acrmatech.com,www.seedling.acrmatech.com,127.0.0.1,localhost,*').split(',') if host.strip()]

CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'https://seedling.acrmatech.com,http://seedling.acrmatech.com').split(',') if origin.strip()]

# Application definition
INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    # Local apps
    'accounts.apps.AccountsConfig',
    'nursery.apps.NurseryConfig',
    'devices.apps.DevicesConfig',
    'monitoring.apps.MonitoringConfig',
    'alerts.apps.AlertsConfig',
    'dashboard.apps.DashboardConfig',
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Use dj-database-url if DATABASE_URL is set (Production/Cloud PostgreSQL), else SQLite
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise storage configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'devices.authentication.DeviceAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/minute',
        'user': '1000/minute',
        'device': '120/minute',
    },
    'EXCEPTION_HANDLER': 'api.exceptions.custom_exception_handler',
}



# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:8000,http://localhost:8000,http://10.125.32.249:8000').split(',')
    if origin.strip()
]

# Login / Logout Redirects
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'login'


def get_unfold_navigation(request):
    """Dynamic sidebar navigation tailored strictly by user role & individual feature toggles."""
    u = getattr(request, 'user', None)
    is_super = u and getattr(u, 'is_super_admin', False)

    management_items = []
    if is_super or getattr(u, 'can_access_dashboard', True):
        management_items.append({
            "title": "Live Interactive Dashboard",
            "icon": "dashboard",
            "link": "/dashboard/",
        })
    if is_super or getattr(u, 'can_access_telemetry', True):
        management_items.append({
            "title": "Sensor Telemetry Readings",
            "icon": "sensors",
            "link": "/admin/monitoring/sensorreading/",
        })
    if is_super or getattr(u, 'can_access_alerts', True):
        management_items.append({
            "title": "System Alerts & Warnings",
            "icon": "notifications_active",
            "link": "/admin/alerts/alert/",
        })
    if is_super or getattr(u, 'can_access_nurseries', True):
        management_items.append({
            "title": "Nurseries",
            "icon": "agriculture",
            "link": "/admin/nursery/nursery/",
        })
    if is_super or getattr(u, 'can_access_zones', True):
        management_items.append({
            "title": "Nursery Zones",
            "icon": "grid_view",
            "link": "/admin/nursery/nurseryzone/",
        })
    if is_super or getattr(u, 'can_access_irrigation', True):
        management_items.append({
            "title": "Irrigation Settings",
            "icon": "water_drop",
            "link": "/admin/devices/devicesetting/",
        })
    if is_super or getattr(u, 'can_access_batches', True):
        management_items.append({
            "title": "Seedling Batches",
            "icon": "potted_plant",
            "link": "/admin/nursery/seedlingbatch/",
        })

    nav = [
        {
            "title": "Smart Nursery Management",
            "separator": True,
            "items": management_items,
        }
    ]

    # Only Super Admin sees System Administration & User Management
    if is_super:
        nav.append({
            "title": "System Administration (Super Admin Only)",
            "separator": True,
            "items": [
                {
                    "title": "ESP32 Hardware Provisioning",
                    "icon": "developer_board",
                    "link": "/admin/devices/device/",
                },
                {
                    "title": "User Accounts & Roles",
                    "icon": "person",
                    "link": "/admin/accounts/user/",
                },
                {
                    "title": "Security Activity Logs",
                    "icon": "history",
                    "link": "/admin/accounts/activitylog/",
                },
            ],
        })

    return nav



# Django Unfold Configuration
UNFOLD = {
    "SITE_TITLE": "Smart Seedling IoT Platform",
    "SITE_HEADER": "Smart Seedling Administration",
    "SITE_SYMBOL": "eco",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "THEME": "light",
    "STYLES": [
        lambda request: static("css/admin_harvesta.css"),
    ],
    "COLORS": {
        "primary": {
            "50": "240 253 244",
            "100": "220 252 231",
            "200": "187 247 208",
            "300": "134 239 172",
            "400": "74 222 128",
            "500": "34 197 94",
            "600": "22 163 74",
            "700": "21 128 61",
            "800": "22 101 52",
            "900": "20 83 45",
            "950": "5 46 22",
        },
    },
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": get_unfold_navigation,
    },
}
