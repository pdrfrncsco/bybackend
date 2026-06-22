# config/settings/__init__.py
# Settings package entry point

import os

# If DJANGO_SETTINGS_MODULE is config.settings (default set by manage.py),
# dynamically import the correct settings file based on DJANGO_ENV or default to development.
settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings')

if settings_module == 'config.settings':
    django_env = os.environ.get('DJANGO_ENV', 'development').lower()
    if django_env == 'production':
        from .production import *
    elif django_env == 'testing':
        from .testing import *
    else:
        from .development import *
