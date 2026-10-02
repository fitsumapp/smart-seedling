"""
cPanel Phusion Passenger WSGI entry point for Smart Seedling.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add current working directory and project root to Python sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load .env variables
load_dotenv(BASE_DIR / '.env')

# Point to Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
