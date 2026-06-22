from django.urls import reverse
from rest_framework.test import APITestCase, APIClient

from core.models import Tenant
from usuarios.models import User


class OrganizationMeTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Old Name',
            slug='old-slug',
            type='league',
            country='Old Country',
            location='Old Location',
            email='old@example.com',
            phone='000000000',
            website='https://old.example.com',
            description='Old description',
            is_public=True,
        )
        self.user = User.objects.create_user(
            username='org-user',
            email='user@example.com',
            password='testpass123',
            tenant=self.tenant,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_update_me_updates_organization_fields(self):
        url = '/api/organizations/me/'
        payload = {
            'name': 'New Name',
            'primary_color': '#000001',
            'secondary_color': '#ffffff',
            'country': 'Angola',
            'location': 'Luanda',
            'email': 'new@example.com',
            'phone': '+244 923 111 222',
            'website': 'https://new.example.com',
            'description': 'New description',
            'is_public': False,
        }

        response = self.client.put(url, payload, format='json')

        self.assertEqual(response.status_code, 200)

        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.name, 'New Name')
        self.assertEqual(self.tenant.primary_color, '#000001')
        self.assertEqual(self.tenant.secondary_color, '#ffffff')
        self.assertEqual(self.tenant.country, 'Angola')
        self.assertEqual(self.tenant.location, 'Luanda')
        self.assertEqual(self.tenant.email, 'new@example.com')
        self.assertEqual(self.tenant.phone, '+244 923 111 222')
        self.assertEqual(self.tenant.website, 'https://new.example.com')
        self.assertEqual(self.tenant.description, 'New description')
        self.assertFalse(self.tenant.is_public)
