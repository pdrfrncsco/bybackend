from dotenv import load_dotenv
import os
from importlib import import_module

env_path = r'D:\\ndeascloud\\boayetu\\backend\\.env'
load_dotenv(env_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings

print('Using settings.DEFAULT_FILE_STORAGE =', settings.DEFAULT_FILE_STORAGE)
module_name, clsname = settings.DEFAULT_FILE_STORAGE.rsplit('.',1)
mod = import_module(module_name)
cls = getattr(mod, clsname)
print('Storage class:', cls)
try:
    storage = cls()
    print('Instantiated storage class OK:', storage.__class__)
    from django.core.files.base import ContentFile
    content = ContentFile(b'bolayetu-r2-direct-test')
    fname = 'tests/direct_bolayetu_r2_test.txt'
    name = storage.save(fname, content)
    print('Saved name:', name)
    try:
        url = storage.url(name)
    except Exception as e:
        url = f'could not get URL: {e}'
    print('URL:', url)
except Exception as e:
    print('Storage operation failed:', repr(e))
