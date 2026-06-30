from dotenv import load_dotenv
import os

env_path = r'D:\\ndeascloud\\boayetu\\backend\\.env'
print('Loading .env from', env_path)
load_dotenv(env_path)
# Ensure DJANGO_SETTINGS_MODULE is set before setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Create a small test file
content = ContentFile(b'bolayetu-r2-test')
filename = 'tests/bolayetu_r2_test.txt'
print('Using storage:', type(default_storage))
try:
    name = default_storage.save(filename, content)
    print('Saved name:', name)
    try:
        url = default_storage.url(name)
    except Exception as e:
        url = f'Could not get URL: {e}'
    print('URL:', url)
except Exception as e:
    print('Upload failed:', repr(e))
