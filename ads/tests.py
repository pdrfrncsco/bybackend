from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from usuarios.models import User
from core.models import Tenant
from ads.models import Advertisement


class AdvertisementApiTests(APITestCase):
    def setUp(self):
        # Tenant e User Normal
        self.tenant = Tenant.objects.create(name='Test Org', slug='test-org')
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='password123',
            name='User',
            role='manager',
            tenant=self.tenant,
        )
        
        # Ads Manager (Sem tenant)
        self.ads_manager = User.objects.create_user(
            username='adsmanager',
            email='ads@example.com',
            password='password123',
            name='Ads Manager',
            role='ads_manager',
            tenant=None
        )

    def test_create_advertisement_permission(self):
        """Apenas Ads Manager/Superadmin deve criar ads"""
        url = reverse('advertisement-list')
        payload = {
            'title': 'Test Ad',
            'client_name': 'Client',
            'image_url': 'https://example.com/banner.png',
            'link_url': 'https://example.com',
            'placement': 'banner_top',
            'status': 'active',
        }
        
        # Tentativa com usuário normal (Manager)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Tentativa com Ads Manager
        self.client.force_authenticate(user=self.ads_manager)
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        ad = Advertisement.objects.first()
        self.assertEqual(ad.title, 'Test Ad')
        self.assertIsNone(ad.tenant)  # Deve ser global (tenant=None)

    def test_public_read_access(self):
        """Qualquer um deve poder ver anúncios ativos"""
        # Criar ads
        Advertisement.objects.create(
            title='Active Ad',
            image_url='http://url.com',
            link_url='http://link.com',
            status='active',
            tenant=None
        )
        Advertisement.objects.create(
            title='Inactive Ad',
            image_url='http://url.com',
            link_url='http://link.com',
            status='inactive',
            tenant=None
        )
        
        url = reverse('advertisement-list')
        
        # Acesso Anônimo
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Active Ad')
        
    def test_manager_read_access(self):
        """Ads Manager vê tudo"""
        Advertisement.objects.create(
            title='Inactive Ad',
            image_url='http://url.com',
            link_url='http://link.com',
            status='inactive',
            tenant=None
        )
        
        url = reverse('advertisement-list')
        self.client.force_authenticate(user=self.ads_manager)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1) # Vê o inativo
