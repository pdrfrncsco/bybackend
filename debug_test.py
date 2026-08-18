#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from players.models import Player
from datetime import date
import traceback

# Safe local smoke test: do not delete persisted data from the database.
# The previous version used Tenant.objects.all().delete() and Player.objects.all().delete(),
# which explains why clubs/players were disappearing during manual debugging.
Tenant = __import__('core.models', fromlist=['Tenant']).Tenant

# Create test data
tenant = Tenant.objects.create(name='TestTenant', slug='test-tenant-unique')
player = Player.objects.create(
    first_name='John', last_name='Doe', slug='john-doe',
    date_of_birth=date(2000, 1, 15),
    nationality='PT', primary_position='ST', status='active'
)

# Test API
client = APIClient()
try:
    response = client.get('/api/v1/players/')
    print(f'Status: {response.status_code}')
    if response.status_code == 500:
        print(f'Content: {response.content.decode()}')
    else:
        print(f'Success!')
except Exception:
    traceback.print_exc()

