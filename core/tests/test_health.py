"""
BOLAYETU — Health Check API Tests
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class HealthAPITest(APITestCase):
    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], "ok")

    def test_liveness_endpoint(self):
        response = self.client.get(reverse("health-liveness"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], "alive")

    def test_readiness_endpoint(self):
        response = self.client.get(reverse("health-readiness"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["status"], "ready")
