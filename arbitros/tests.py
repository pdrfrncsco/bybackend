from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Tenant
from usuarios.models import User
from .models import Referee

class RefereeApiTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name='Tenant Teste', slug='tenant-teste')
        self.user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123',
            role='manager',
            tenant=self.tenant,
        )
        self.client.force_authenticate(self.user)

    def test_create_referee(self):
        url = reverse('referee-list')
        payload = {
            'name': 'Árbitro Teste',
            'bi': 'BI12345',
            'category': 'national',
            'phone': '+244900000000',
            'email': 'ref@example.com',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Referee.objects.filter(tenant=self.tenant).count(), 1)
        obj = Referee.objects.get(tenant=self.tenant)
        self.assertEqual(obj.name, 'Árbitro Teste')
