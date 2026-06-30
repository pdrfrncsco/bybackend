from dotenv import load_dotenv
import os

env_path = r'D:\\ndeascloud\\boayetu\\backend\\.env'
print('Loading .env from', env_path)
load_dotenv(env_path)
print('ENV USE_CLOUDFLARE_R2=', os.environ.get('USE_CLOUDFLARE_R2'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
print('settings.USE_CLOUDFLARE_R2 =', settings.USE_CLOUDFLARE_R2)
print('settings.DEFAULT_FILE_STORAGE =', settings.DEFAULT_FILE_STORAGE)
from django.core.files.storage import default_storage
print('default_storage class =', default_storage.__class__)
print('default_storage location attr (if any) =', getattr(default_storage, 'location', None))
