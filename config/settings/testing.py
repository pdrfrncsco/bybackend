"""
BOLAYETU — Testing Settings
Use: DJANGO_SETTINGS_MODULE=config.settings.testing
"""

from .base import *

DEBUG = True
SECRET_KEY = 'testing-secret-key-not-for-production'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'bolayetu_test'),
        'USER': os.environ.get('POSTGRES_USER', 'bolayetu'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'bolayetu_test_pass'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'test_media'

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

CORS_ALLOW_ALL_ORIGINS = True

# Speed up tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable throttling in tests
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
