"""
BOLAYETU — Development Settings
Use: DJANGO_SETTINGS_MODULE=config.settings.development
"""

from .base import *

# ===================================================================
# CORE
# ===================================================================

DEBUG = True

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-only-not-for-production-change-me'
)

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '.localhost',  # Subdomain support for local dev
    '.bolayetu.local',
]

# ===================================================================
# DATABASE — PostgreSQL (Docker)
# ===================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'bolayetu_dev'),
        'USER': os.environ.get('POSTGRES_USER', 'bolayetu'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'bolayetu_dev_pass'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),  # Docker service name
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

# ===================================================================
# CACHE — Redis (Docker)
# ===================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'bolayetu_dev',
    }
}

# ===================================================================
# CELERY — Redis broker
# ===================================================================

CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# ===================================================================
# MEDIA STORAGE — Local in development
# ===================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===================================================================
# CORS — Wide open in development
# ===================================================================

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ===================================================================
# EMAIL — Console backend in development
# ===================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ===================================================================
# DEBUG TOOLBAR (optional — install django-debug-toolbar)
# ===================================================================

# Uncomment if you install django-debug-toolbar:
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ['127.0.0.1']

# ===================================================================
# JWT — Longer lifetime in dev for convenience
# ===================================================================

from datetime import timedelta
SIMPLE_JWT = {
    **SIMPLE_JWT,
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# ===================================================================
# DRF — Throttle off in development
# ===================================================================

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_CLASSES': [],  # No throttling in dev
}

# ===================================================================
# DJANGO EXTENSIONS / DEV TOOLS
# ===================================================================

LOGGING['loggers']['django.db.backends']['level'] = 'WARNING'

# Tenant middleware config for local development
# Map local test subdomains: girabola.bolayetu.local → slug girabola
BOLAYETU_DOMAIN = os.environ.get('BOLAYETU_DOMAIN', 'bolayetu.local')
