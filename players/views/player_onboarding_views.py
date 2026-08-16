from rest_framework import generics, permissions
from rest_framework.response import Response
from django.http import Http404

from players.models import PlayerOnboardingStatus
from players.serializers.player_onboarding import PlayerOnboardingStatusSerializer
from players.services import NoPlayerProfile, PlayerService
from players.services.onboarding_service import PlayerOnboardingService


class PlayerOnboardingStatusView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = PlayerOnboardingStatusSerializer

    def get_object(self):
        try:
            player = PlayerService.get_player_for_user(self.request.user)
        except NoPlayerProfile:
            raise Http404
        return PlayerOnboardingService.get_status(player)


class PlayerOnboardingCompleteStepView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PlayerOnboardingStatusSerializer

    def get_object(self):
        player = PlayerService.get_player_for_user(self.request.user)
        return PlayerOnboardingService.get_status(player)

    def patch(self, request, *args, **kwargs):
        step = request.data.get('step')
        if not step:
            return Response({'detail': 'step is required'}, status=400)
        player = PlayerService.get_player_for_user(request.user)
        try:
            status = PlayerOnboardingService.complete_step(player=player, step=step)
        except ValueError:
            return Response({'detail': 'unknown step'}, status=400)

        from common.responses import success_response
        from players.views.player_me_views import build_onboarding_status_data
        data = build_onboarding_status_data(player, status)
        return success_response(data=data, message=f"Step '{step}' marked complete.")
