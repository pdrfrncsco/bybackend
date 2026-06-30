import os
import time
import unittest
from importlib import import_module

# Load .env early so Django settings pick up the variables during import
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

from django.test import TestCase
from django.conf import settings
from django.core.files.base import ContentFile

# Decide whether to run the test: prefer explicit env var, fall back to settings
RUN_R2_ENV = os.environ.get("USE_CLOUDFLARE_R2", "").lower() in ("true", "1", "yes")
RUN_R2_SETTING = getattr(settings, "USE_CLOUDFLARE_R2", False)
HAS_DEFAULT_STORAGE = hasattr(settings, 'DEFAULT_FILE_STORAGE')

RUN_R2 = (RUN_R2_ENV or RUN_R2_SETTING) and HAS_DEFAULT_STORAGE

@unittest.skipUnless(RUN_R2, "Cloudflare R2 not enabled in environment/settings or DEFAULT_FILE_STORAGE not configured")
class R2StorageTest(TestCase):
    """Smoke test: save and delete a small file using the configured DEFAULT_FILE_STORAGE.

    This test validates that the S3/Django storage configured for Cloudflare R2
    can save a file and produce a URL. It cleans up the object afterwards.
    """

    def test_upload_and_delete_r2(self):
        module_name, clsname = settings.DEFAULT_FILE_STORAGE.rsplit('.', 1)
        mod = import_module(module_name)
        cls = getattr(mod, clsname)

        storage = cls()
        content = ContentFile(b'bolayetu-r2-test')
        fname = f'org-tests/bolayetu_r2_test_{int(time.time())}.txt'

        # Save
        name = storage.save(fname, content)
        self.assertTrue(name, "Storage did not return a saved name")

        # URL
        try:
            url = storage.url(name)
        except Exception as e:
            self.fail(f"storage.url() raised an exception: {e}")

        self.assertIsInstance(url, str)
        self.assertTrue(url, "storage.url() returned empty string")

        # Basic sanity: bucket name appears in URL when configured
        bucket = os.environ.get('CLOUDFLARE_R2_BUCKET') or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
        if bucket:
            self.assertIn(bucket, url)

        # Cleanup
        try:
            storage.delete(name)
        except Exception as e:
            self.fail(f"storage.delete() failed: {e}")
