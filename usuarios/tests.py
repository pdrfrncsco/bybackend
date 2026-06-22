from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(APITestCase):
    def test_register_user(self):
        """
        Ensure we can register a new user.
        """
        url = reverse('auth_register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'strongpassword123',
            'name': 'Test User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')

    def test_login_user(self):
        """
        Ensure we can login and get a JWT token.
        """
        # Create user first
        user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='strongpassword123',
            name='Test User'
        )
        
        url = reverse('auth_login')
        data = {
            'username': 'testuser',
            'password': 'strongpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verify custom claims
        import jwt
        token = response.data['access']
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        self.assertEqual(decoded_token['name'], 'Test User')

    def test_get_me_protected(self):
        """
        Ensure the /me/ endpoint is protected and returns user data.
        """
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        url = reverse('auth_me')
        
        # Try without auth
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Authenticate
        self.client.force_authenticate(user=user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
