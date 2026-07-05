import importlib
import os
import sys
import unittest
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase


class R2SettingsValidationTest(SimpleTestCase):
    def test_r2_requires_cdn_url(self):
        module_name = "config.settings"
        original_module = sys.modules.pop(module_name, None)

        try:
            with patch.dict(
                os.environ,
                {
                    "USE_CLOUDFLARE_R2": "True",
                    "CLOUDFLARE_R2_ENDPOINT": "https://example.r2.cloudflarestorage.com",
                    "CLOUDFLARE_R2_ACCESS_KEY_ID": "test-access-key",
                    "CLOUDFLARE_R2_SECRET_ACCESS_KEY": "test-secret-key",
                    "CLOUDFLARE_R2_BUCKET": "test-bucket",
                    "CLOUDFLARE_R2_CDN_URL": "",
                },
                clear=False,
            ):
                with self.assertRaises(ImproperlyConfigured):
                    importlib.import_module(module_name)
        finally:
            sys.modules.pop(module_name, None)
            if original_module is not None:
                sys.modules[module_name] = original_module

    def test_r2_imports_with_cdn_url(self):
        module_name = "config.settings"
        original_module = sys.modules.pop(module_name, None)

        try:
            with patch.dict(
                os.environ,
                {
                    "USE_CLOUDFLARE_R2": "True",
                    "CLOUDFLARE_R2_ENDPOINT": "https://example.r2.cloudflarestorage.com",
                    "CLOUDFLARE_R2_ACCESS_KEY_ID": "test-access-key",
                    "CLOUDFLARE_R2_SECRET_ACCESS_KEY": "test-secret-key",
                    "CLOUDFLARE_R2_BUCKET": "test-bucket",
                    "CLOUDFLARE_R2_CDN_URL": "https://cdn.example.com",
                },
                clear=False,
            ):
                module = importlib.import_module(module_name)
                self.assertEqual(module.CLOUDFLARE_R2_CDN_URL, "https://cdn.example.com")
        finally:
            sys.modules.pop(module_name, None)
            if original_module is not None:
                sys.modules[module_name] = original_module
