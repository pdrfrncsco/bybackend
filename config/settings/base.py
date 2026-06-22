"""
BOLAYETU — Base Settings
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL

Princípios:
- Toda a lógica de negócio pertence ao Service Layer
- Toda a leitura de dados pertence ao Selector Layer
- NUNCA colocar lógica em Views ou Serializers
- SEMPRE isolar por tenant em todos os querysets
"""

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env files
load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR.parent / '.env')

# ===================================================================
# CORE
# ===================================================================

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-me-immediately')
DEBUG = False
ALLOWED_HOSTS = []

# ===================================================================
# INSTALLED APPS
# ===================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    'django_filters',
    'storages',
]

LOCAL_APPS = [
    # Infrastructure
    'core',

    # Identity & Access (Bounded Context 1)
    'accounts',
    'usuarios',
    'onboarding',

    # Tenant Management (Bounded Context 2)
    'affiliations',
    'assinaturas',

    # Competition Management (Bounded Context 3)
    'torneios',
    'partidas',
    'classificacoes',
    'matchengine',
    'estatisticas',

    # Club & Squad Management (Bounded Context 4)
    'clubes',
    'treinadores',
    'arbitros',
    'estadios',

    # Player Career (Bounded Context 5)
    'jogadores',

    # Fan Engagement (Bounded Context 6)
    'fanportal',
    'notifications',
    'news',

    # Platform
    'organizacoes',
    'dashboard',
    'definicoes',
    'relatorios',
    'publico',
    'ads',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ===================================================================
# MIDDLEWARE
# ===================================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # ─── Bolayetu Custom Middleware ───────────────────────────────
    # IMPORTANT: TenantMiddleware MUST come AFTER AuthenticationMiddleware
    # It resolves request.tenant from the subdomain (e.g. girabola.bolayetu.com)
    'core.middleware.TenantMiddleware',
    'core.middleware.AuthTrackingMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ===================================================================
# URLS & WSGI
# ===================================================================

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ===================================================================
# TEMPLATES
# ===================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# ===================================================================
# AUTHENTICATION
# ===================================================================

AUTH_USER_MODEL = 'usuarios.User'

AUTHENTICATION_BACKENDS = [
    'usuarios.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===================================================================
# JWT — Token rotation ENABLED (security requirement)
# ===================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # SECURITY: Always rotate refresh tokens on use
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}

# ===================================================================
# REST FRAMEWORK
# ===================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
        'djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'djangorestframework_camel_case.parser.CamelCaseFormParser',
        'djangorestframework_camel_case.parser.CamelCaseMultiPartParser',
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardResultsPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    'EXCEPTION_HANDLER': 'common.exceptions.bolayetu_exception_handler',
}

# ===================================================================
# API DOCUMENTATION
# ===================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'Bolayetu API',
    'DESCRIPTION': 'Football Ecosystem Platform — Angola & Africa',
    'VERSION': '2.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication & Authorization'},
        {'name': 'organizations', 'description': 'Organization management'},
        {'name': 'clubs', 'description': 'Club management'},
        {'name': 'players', 'description': 'Player profiles & careers'},
        {'name': 'competitions', 'description': 'Competition management'},
        {'name': 'matches', 'description': 'Match management'},
        {'name': 'rankings', 'description': 'Rankings & standings'},
        {'name': 'transfers', 'description': 'Player transfers'},
        {'name': 'news', 'description': 'News & media'},
        {'name': 'notifications', 'description': 'Push notifications'},
    ],
}

# ===================================================================
# STATIC FILES
# ===================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ===================================================================
# INTERNATIONALISATION
# ===================================================================

LANGUAGE_CODE = 'pt-ao'
TIME_ZONE = 'Africa/Luanda'
USE_I18N = True
USE_TZ = True

# ===================================================================
# DEFAULT PRIMARY KEY
# ===================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===================================================================
# EXTERNAL SERVICES PLACEHOLDERS
# ===================================================================

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@bolayetu.ao')

# Bolayetu domain config — used by TenantMiddleware
BOLAYETU_DOMAIN = os.environ.get('BOLAYETU_DOMAIN', 'bolayetu.com')
BOLAYETU_RESERVED_SUBDOMAINS = ['www', 'app', 'api', 'admin', 'cdn', 'mail', 'smtp', 'ftp']

# Upload limits
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DATA_UPLOAD_MAX_MEMORY_SIZE', 26214400))  # 25 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE

MCX_API_URL = os.environ.get('MCX_API_URL', 'MOCK')
UNITEL_API_URL = os.environ.get('UNITEL_API_URL', 'MOCK')
UNITEL_API_KEY = os.environ.get('UNITEL_API_KEY', 'MOCK')

# ===================================================================
# LOGGING — stdout friendly (Docker compatible)
# ===================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Set to DEBUG to log all SQL
            'propagate': False,
        },
        'bolayetu': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'access': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
