"""
BOLAYETU — Production Settings
Use: DJANGO_SETTINGS_MODULE=config.settings.production

Skills: BOLAYETU_SECURITY_SKILL, BOLAYETU_CLOUDFLARE_SKILL, BOLAYETU_DOCKER_DEVOPS_SKILL
"""

from .base import *
import os

# ===================================================================
# CORE SECURITY
# ===================================================================

DEBUG = False

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # MUST be set — fails if missing

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
    if host.strip()
]

# ===================================================================
# DATABASE — PostgreSQL (mandatory in production)
# ===================================================================

if not os.environ.get('POSTGRES_DB'):
    raise RuntimeError(
        "POSTGRES_DB not set — production cannot start without PostgreSQL. "
        "SQLite is forbidden in production."
    )

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'sslmode': os.environ.get('POSTGRES_SSLMODE', 'prefer'),
        },
    }
}

# ===================================================================
# CACHE — Redis (mandatory in production)
# ===================================================================

REDIS_URL = os.environ['REDIS_URL']  # MUST be set

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        },
        'KEY_PREFIX': 'bolayetu_prod',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ===================================================================
# CELERY — Redis broker in production
# ===================================================================

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# ===================================================================
# MEDIA STORAGE — Cloudflare R2 (mandatory — no local storage)
# Skill: BOLAYETU_CLOUDFLARE_SKILL
#
# FORBIDDEN: MEDIA_ROOT, local file storage
# REQUIRED: All files → R2 → served via cdn.bolayetu.com
# ===================================================================

DEFAULT_FILE_STORAGE = 'infrastructure.storage.r2_storage.R2PublicStorage'

# Cloudflare R2 credentials (S3-compatible API)
AWS_ACCESS_KEY_ID = os.environ['CLOUDFLARE_R2_ACCESS_KEY']
AWS_SECRET_ACCESS_KEY = os.environ['CLOUDFLARE_R2_SECRET_KEY']
AWS_STORAGE_BUCKET_NAME = os.environ['CLOUDFLARE_R2_BUCKET']
AWS_S3_ENDPOINT_URL = os.environ['CLOUDFLARE_R2_ENDPOINT']

# CDN domain — files served via Cloudflare CDN, NOT raw R2 URLs
AWS_S3_CUSTOM_DOMAIN = os.environ.get('CLOUDFLARE_CDN_DOMAIN', 'cdn.bolayetu.com')

# Public media URL via CDN
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"

# Aggressive cache headers for media files (1 year)
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=31536000, s-maxage=31536000, public',
}

AWS_QUERYSTRING_AUTH = False  # Public files — no signed URLs needed
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = False  # Never overwrite — use unique filenames

# Private storage for documents (signed URLs)
PRIVATE_FILE_STORAGE = 'infrastructure.storage.r2_storage.R2PrivateStorage'

# ===================================================================
# STATIC FILES — WhiteNoise for Django admin + docs
# ===================================================================

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# ===================================================================
# CORS — Strict in production
# ===================================================================

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-tenant-slug',
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if origin.strip()
]

# ===================================================================
# SECURITY HEADERS
# ===================================================================

SECURE_SSL_REDIRECT = False  # Nginx handles SSL
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ===================================================================
# EMAIL — SMTP in production
# ===================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@bolayetu.ao')

# ===================================================================
# DRF — Strict throttling in production
# ===================================================================

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'common.throttling.TenantRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '200/hour',
        'user': '2000/hour',
        'tenant': '10000/hour',
    },
}

# ===================================================================
# LOGGING — stdout only (Docker/container friendly)
# Skill: BOLAYETU_DOCKER_DEVOPS_SKILL — "Logs must be container friendly"
# ===================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'bolayetu': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'access': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'celery': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

# ===================================================================
# TENANT CONFIG
# ===================================================================

BOLAYETU_DOMAIN = os.environ.get('BOLAYETU_DOMAIN', 'bolayetu.com')
