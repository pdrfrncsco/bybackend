from rest_framework import viewsets, permissions
from .models import Stadium
from .serializers import StadiumSerializer
from core.permissions import IsManager

class StadiumViewSet(viewsets.ModelViewSet):
    serializer_class = StadiumSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Stadium.objects.none()
        user = getattr(self.request, "user", None)
        tenant = getattr(user, "tenant", None)
        if not tenant:
            return Stadium.objects.none()
        return Stadium.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        user = getattr(self.request, "user", None)
        tenant = getattr(user, "tenant", None)
        if tenant:
            serializer.save(tenant=tenant)
