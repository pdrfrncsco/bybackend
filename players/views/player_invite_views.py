from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from datetime import date

from common.responses import success_response, error_response
from players.serializers.player_invite import PlayerInviteSerializer
from players.services.invite_service import PlayerInviteService
from players.serializers import PlayerSerializer
from players.models import Player
from players.services import NoPlayerProfile, PlayerService


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


class RedeemInviteView(APIView):
    """Redeem an invite token.

    - If authenticated: create and link a Player to the current user (if none exists) and optionally create a registration for the invited club.
    - If anonymous: return prefilled invite data for the signup flow.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return error_response(message='token is required', status_code=400)

        invite = PlayerInviteService.redeem_invite(token)
        if not invite:
            return error_response(message='Invalid or expired token', status_code=404)

        # If user is anonymous, return invite data for signup prefill
        if not request.user or not request.user.is_authenticated:
            data = {
                'email': invite.email,
                'first_name': invite.first_name,
                'last_name': invite.last_name,
                'token': str(invite.token),
            }
            return success_response(data=data, message='Invite retrieved')

        # Authenticated user: link/create player
        try:
            # If user already has a player, prevent linking
            player = PlayerService.get_player_for_user(request.user)
            return error_response(message='User already has a linked player profile', status_code=409)
        except NoPlayerProfile:
            # OK to create
            pass

        # Build player data
        first_name = invite.first_name or (invite.email.split('@')[0] if invite.email else 'Player')
        last_name = invite.last_name or ''
        email = invite.email

        # Create Player
        try:
            player = Player.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                user=request.user,
                status=Player.PlayerStatus.ACTIVE,
            )
        except Exception as e:
            return error_response(message=f'Failed to create player: {e}', status_code=400)

        # Optionally create PlayerRegistration if club invited
        if invite.club_id:
            try:
                from players.models import PlayerRegistration
                from django.utils import timezone
                club = invite.club
                PlayerRegistration.objects.create(
                    player=player,
                    club=club,
                    tenant=club.tenant,
                    joined_date=timezone.now().date(),
                    status=PlayerRegistration.RegistrationStatus.REGISTERED,
                )
            except Exception as e:
                # Non-fatal: log and continue
                # (in production prefer a logger)
                print('Warning: failed to create registration from invite:', e)

        # Return created player
        serializer = PlayerSerializer(player)
        return success_response(data=serializer.data, message='Player profile created and linked from invite')
