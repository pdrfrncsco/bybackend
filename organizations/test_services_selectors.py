from django.test import TestCase
from core.models import Tenant
from usuarios.models import User
from clubs.models import Club, ClubHistory
from torneios.models import Tournament
from organizations.services import OrganizationService
from organizations.selectors import OrganizationSelector



class OrganizationServiceSelectorTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant',
            type='league',
            is_public=True,
        )
        self.user = User.objects.create_user(
            username='test-user',
            email='test@example.com',
            password='password123',
            tenant=self.tenant,
        )

    def test_update_organization(self):
        service = OrganizationService(user=self.user, tenant=self.tenant)
        data = {
            'name': 'Updated Tenant Name',
            'primary_color': '#FF5733',
            'secondary_color': '#33FF57',
        }
        updated = service.update_organization(self.tenant, data=data)
        self.assertEqual(updated.name, 'Updated Tenant Name')
        self.assertEqual(updated.primary_color, '#FF5733')
        self.assertEqual(updated.secondary_color, '#33FF57')

    def test_subscribe_unsubscribe(self):
        service = OrganizationService(user=self.user)
        self.assertEqual(self.user.subscriptions.count(), 0)

        service.subscribe_user(tenant=self.tenant)
        self.assertEqual(self.user.subscriptions.count(), 1)
        self.assertIn(self.tenant, self.user.subscriptions.all())

        service.unsubscribe_user(tenant=self.tenant)
        self.assertEqual(self.user.subscriptions.count(), 0)

    def test_selector_list_public_organizations(self):
        # Create another private tenant
        private_tenant = Tenant.objects.create(
            name='Private Tenant',
            slug='private-tenant',
            type='federation',
            is_public=False,
        )
        
        selector = OrganizationSelector()
        public_orgs = list(selector.list_public_organizations())
        
        self.assertIn(self.tenant, public_orgs)
        self.assertNotIn(private_tenant, public_orgs)

    def test_selector_get_organization_tournaments(self):
        t1 = Tournament.objects.create(
            tenant=self.tenant,
            name='Girabola 2026',
            season='2026',
            status='active',
            is_public=True,
            start_date='2026-01-01',
        )
        t2 = Tournament.objects.create(
            tenant=self.tenant,
            name='Angola Cup',
            season='2026',
            status='upcoming',
            is_public=False,
            start_date='2026-01-01',
        )
        
        selector = OrganizationSelector()
        tournaments = list(selector.get_organization_tournaments(self.tenant, is_public=True))
        self.assertIn(t1, tournaments)
        self.assertNotIn(t2, tournaments)
