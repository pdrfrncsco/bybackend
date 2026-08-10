from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from players.serializers.player_invite import PlayerInviteSerializer
from players.services.invite_service import PlayerInviteService


class InvitePlayerView(generics.CreateAPIView):
    """Admin-only endpoint to create player invites."""

    serializer_class = PlayerInviteSerializer
    permission_classes = [permissions.IsAdminUser]

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        club_id = request.data.get('club')

        if not email:
            return Response({'detail': 'email is required'}, status=status.HTTP_400_BAD_REQUEST)

        invited_by = request.user
        # Club resolution left to ForeignKey validation in serializer/migration; accept club id directly
        invite = PlayerInviteService.create_invite(email=email, first_name=first_name, last_name=last_name, invited_by=invited_by, club=club_id)
        serializer = PlayerInviteSerializer(invite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
