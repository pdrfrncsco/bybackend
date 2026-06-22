from .settings import *
import os
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
# =====================================================
# CORE SECURITY
# =====================================================

DEBUG = False

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if host.strip()]

# =====================================================
# DATABASE (POSTGRESQL OBRIGATÓRIO)
# =====================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

# 🔥 Segurança: se não houver Postgres, falha imediatamente
if not os.environ.get('POSTGRES_DB'):
    raise RuntimeError("POSTGRES_DB não definido – produção abortada")

# =====================================================
# STATIC & MEDIA (Cloudflare R2 configuration)
# =====================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Use Cloudflare R2 (S3-compatible) for media in production
# Expect env vars defined in backend/.env or environment
INSTALLED_APPS += ["storages"]

DEFAULT_FILE_STORAGE = os.environ.get(
    'DEFAULT_FILE_STORAGE', 'storages.backends.s3boto3.S3Boto3Storage'
)

AWS_ACCESS_KEY_ID = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('CLOUDFLARE_R2_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('CLOUDFLARE_R2_BUCKET')
AWS_S3_ENDPOINT_URL = os.environ.get(
    'CLOUDFLARE_R2_ENDPOINT', 'https://e8f032f108e5a93a5a6916c607572a06.r2.cloudflarestorage.com'
)
AWS_S3_CUSTOM_DOMAIN = os.environ.get('CLOUDFLARE_CDN_DOMAIN', 'cdn.bolayetu.com')

# Public CDN URL (used by Django to generate file URLs)
MEDIA_URL = os.environ.get('MEDIA_URL', f"https://{AWS_S3_CUSTOM_DOMAIN}/")

# Ensure files are served with long-lived cache headers by default
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': os.environ.get('AWS_S3_CACHE_CONTROL', 'max-age=31536000, s-maxage=31536000, public')
}

# Keep URLs clean
AWS_QUERYSTRING_AUTH = False
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_DEFAULT_ACL = None
AWS_S3_FILE_OVERWRITE = True

# Optionally set region (Cloudflare typically doesn't need a region)
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', None)

# Adjust upload limits if you handle large files through backend
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', 26214400))  # 25 MB default

# =====================================================
# CORS
# =====================================================

CORS_ALLOW_ALL_ORIGINS = False

# O .strip() remove espaços acidentais e o filter remove entradas vazias
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if origin.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()
]
# =====================================================
# EMAIL
# =====================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

# =====================================================
# SECURITY HEADERS (NGINX + GUNICORN)
# =====================================================

SECURE_SSL_REDIRECT = False
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =====================================================
# LOGGING (ESSENCIAL EM PRODUÇÃO)
# =====================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/www/bolayetu/log/django.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
