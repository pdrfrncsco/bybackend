from dotenv import load_dotenv
import os
from importlib import import_module

env_path = r'D:\\ndeascloud\\boayetu\\backend\\.env'
print('Loading .env from', env_path)
load_dotenv(env_path)
print('ENV USE_CLOUDFLARE_R2=', os.environ.get('USE_CLOUDFLARE_R2'))
print('ENV CLOUDFLARE_R2_ACCESS_KEY_ID=', os.environ.get('CLOUDFLARE_R2_ACCESS_KEY_ID'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings

print('settings.USE_CLOUDFLARE_R2 =', getattr(settings, 'USE_CLOUDFLARE_R2', None))
print('settings.DEFAULT_FILE_STORAGE =', getattr(settings, 'DEFAULT_FILE_STORAGE', None))

# Check if storages backend is importable
try:
    mod = import_module('storages.backends.s3boto3')
    print('storages.backends.s3boto3 available')
except Exception as e:
    print('storages.backends.s3boto3 import failed:', repr(e))

try:
    import boto3
    print('boto3 available, version', getattr(boto3, '__version__', 'unknown'))
except Exception as e:
    print('boto3 import failed:', repr(e))
