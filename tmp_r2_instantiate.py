from dotenv import load_dotenv
import os

env_path = r'D:\\ndeascloud\\boayetu\\backend\\.env'
load_dotenv(env_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
from importlib import import_module

django.setup()
from django.conf import settings
print('settings.DEFAULT_FILE_STORAGE =', settings.DEFAULT_FILE_STORAGE)
try:
    mod = import_module(settings.DEFAULT_FILE_STORAGE.rsplit('.',1)[0])
    clsname = settings.DEFAULT_FILE_STORAGE.rsplit('.',1)[1]
    cls = getattr(mod, clsname)
    print('Got class', cls)
    try:
        inst = cls()
        print('Instantiated storage:', inst.__class__)
    except Exception as e:
        print('Instantiation failed:', repr(e))
except Exception as e:
    print('Import failed:', repr(e))
