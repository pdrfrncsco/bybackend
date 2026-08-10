from rest_framework import generics, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from players.models import Player, PlayerOnboardingStatus
from players.serializers.player_onboarding import PlayerOnboardingStatusSerializer
from players.services.onboarding_service import PlayerOnboardingService


class PlayerOnboardingStatusView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = PlayerOnboardingStatusSerializer

    def get_object(self):
        player = get_object_or_404(Player, user=self.request.user)
        return PlayerOnboardingService.get_status(player)


class PlayerOnboardingCompleteStepView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PlayerOnboardingStatusSerializer

    def get_object(self):
        player = get_object_or_404(Player, user=self.request.user)
        return PlayerOnboardingService.get_status(player)

    def patch(self, request, *args, **kwargs):
        step = request.data.get('step')
        if not step:
            return Response({'detail': 'step is required'}, status=400)
        try:
            status = PlayerOnboardingService.complete_step(player=get_object_or_404(Player, user=request.user), step=step)
        except ValueError:
            return Response({'detail': 'unknown step'}, status=400)
        return Response(PlayerOnboardingStatusSerializer(status).data)
