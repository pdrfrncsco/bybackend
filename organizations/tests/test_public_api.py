from django.test import TestCase, Client


class PublicOrganizationsAPITest(TestCase):
    def test_public_organizations_list_returns_200_and_envelope(self):
        client = Client()
        resp = client.get('/api/v1/organizations/public/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success') is True)
        self.assertIn('data', data)
