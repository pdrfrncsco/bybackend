from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
from core.models import Tenant
from usuarios.models import User
from .models import NewsArticle

class NewsArticleTests(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Org News", slug="org-news")
        self.user = User.objects.create_user(
            username="newsadmin",
            password="password",
            tenant=self.tenant,
            role='manager'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.article1 = NewsArticle.objects.create(
            tenant=self.tenant,
            title="News 1",
            summary="Summary 1",
            content="Content 1",
            author="Admin",
            published_at=timezone.now(),
            status='published',
            category='Comunicado'
        )
        
        self.article2 = NewsArticle.objects.create(
            tenant=self.tenant,
            title="News 2 Draft",
            summary="Summary 2",
            content="Content 2",
            author="Admin",
            published_at=timezone.now(),
            status='draft',
            category='Comunicado'
        )

    def test_list_news_admin(self):
        url = reverse('news-article-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin sees all (draft and published) for their tenant
        self.assertEqual(len(response.data['results']), 2)

    def test_create_news(self):
        url = reverse('news-article-list')
        data = {
            'title': 'New Article',
            'summary': 'Summary',
            'content': 'Content',
            'author': 'Me',
            'publishedAt': timezone.now().isoformat(),
            'status': 'published',
            'category': 'Jogo'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NewsArticle.objects.count(), 3)
        self.assertEqual(NewsArticle.objects.last().tenant, self.tenant)

    def test_public_news_list(self):
        self.client.logout()
        url = reverse('public-news-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Public only sees published
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'News 1')

    def test_increment_views(self):
        self.client.logout()
        url = reverse('public-news-detail', args=[self.article1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.article1.refresh_from_db()
        self.assertEqual(self.article1.views, 1)

    def test_like_news_authenticated_only_once(self):
        url = reverse('public-news-like', args=[self.article1.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.article1.refresh_from_db()
        self.assertEqual(self.article1.likes, 1)

        response_second = self.client.post(url)
        self.assertEqual(response_second.status_code, status.HTTP_200_OK)

        self.article1.refresh_from_db()
        self.assertEqual(self.article1.likes, 1)

    def test_like_news_requires_authentication(self):
        self.client.logout()
        url = reverse('public-news-like', args=[self.article1.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
