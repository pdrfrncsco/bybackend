from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from players.serializers.player_invite import PlayerInviteSerializer
from players.services.invite_service import PlayerInviteService


class InvitePlayerView(generics.CreateAPIView):
    """Endpoint to create player invites.

    Allowed users:
      - Superusers / site admins
      - Club managers/presidents for the target club (must provide club id)
    """

    serializer_class = PlayerInviteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        club_id = request.data.get('club')

        if not email:
            return Response({'detail': 'email is required'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        # Allow superusers
        if user.is_superuser:
            allowed = True
        else:
            # Non-admins must provide a club and be a club admin (manager/president) for that club
            allowed = False
            if club_id:
                try:
                    from clubs.models import ClubMember
                    from clubs.constants import ClubMemberRole

                    is_club_admin = ClubMember.objects.filter(
                        club_id=club_id,
                        user=user,
                        is_active=True,
                        role__in=ClubMemberRole.ADMIN_ROLES,
                    ).exists()
                    if is_club_admin:
                        allowed = True
                except Exception:
                    allowed = False

        if not allowed:
            return Response({'detail': 'You do not have permission to invite players for this club.'}, status=status.HTTP_403_FORBIDDEN)

        invited_by = request.user
        invite = PlayerInviteService.create_invite(email=email, first_name=first_name, last_name=last_name, invited_by=invited_by, club=club_id)
        serializer = PlayerInviteSerializer(invite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
