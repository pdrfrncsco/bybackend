from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from django.shortcuts import get_object_or_404
from competitions.models import TacticalPositions, Match
from clubs.models import Club
from competitions.serializers.tactical_serializers import (
    TacticalPositionsInputSerializer, TacticalPositionsSerializer
)
from competitions.views.lineup_views import get_request_tenant


class TacticalPositionsViewSet(viewsets.ViewSet):
    """ViewSet to handle tactical positions per match."""

    def get_permissions(self):
        # Use default DRF permission flow; custom checks happen in methods
        return []

    def list(self, request, match_id=None):
        return self.retrieve(request, match_id=match_id)

    def retrieve(self, request, match_id=None):
        tenant = get_request_tenant(request)
        club_id = request.query_params.get('club')

        qs = TacticalPositions.objects.filter(match_id=match_id)
        if club_id:
            qs = qs.filter(club_id=club_id)
        if tenant:
            qs = qs.filter(tenant=tenant)
        tp = qs.first()
        if not tp:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TacticalPositionsSerializer({
            'match': str(tp.match_id), 'club': str(tp.club_id), 'positions': tp.positions, 'version': tp.version, 'updated_at': tp.updated_at
        })
        return Response({'data': serializer.data})

    def create(self, request, match_id=None):
        tenant = get_request_tenant(request)
        if tenant is None:
            return Response({"error": "Tenant not identified"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = TacticalPositionsInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        club_id = serializer.validated_data['club']
        positions = serializer.validated_data['positions']
        incoming_version = serializer.validated_data.get('version')

        from clubs.models import ClubMember
        is_allowed = request.user.is_superuser
        if not is_allowed:
            is_allowed = ClubMember.objects.filter(club_id=club_id, user=request.user, is_active=True, role__in=["manager", "coach", "assistant_coach"]).exists()
        if not is_allowed:
            return Response({"error": "User not permitted to modify tactical positions for this club."}, status=status.HTTP_403_FORBIDDEN)

        try:
            tp_qs = TacticalPositions.objects.filter(match_id=match_id, club_id=club_id)
            if tenant:
                tp_qs = tp_qs.filter(tenant=tenant)
            tp_obj = tp_qs.first()

            if tp_obj:
                if incoming_version and str(tp_obj.version) != str(incoming_version):
                    return Response({'detail': 'Conflict', 'data': {
                        'match': str(tp_obj.match_id), 'club': str(tp_obj.club_id), 'positions': tp_obj.positions, 'version': tp_obj.version, 'updated_at': tp_obj.updated_at
                    }}, status=status.HTTP_409_CONFLICT)

                tp_obj.positions = positions
                tp_obj.touch_version()
                tp_obj.save()
                serializer_out = TacticalPositionsSerializer({
                    'match': str(tp_obj.match_id), 'club': str(tp_obj.club_id), 'positions': tp_obj.positions, 'version': tp_obj.version, 'updated_at': tp_obj.updated_at
                })
                return Response({'data': serializer_out.data}, status=status.HTTP_200_OK)
            else:
                club = Club.objects.get(id=club_id)
                tp_new = TacticalPositions.objects.create(tenant=tenant, match_id=match_id, club=club, positions=positions)
                serializer_out = TacticalPositionsSerializer({
                    'match': str(tp_new.match_id), 'club': str(tp_new.club_id), 'positions': tp_new.positions, 'version': tp_new.version, 'updated_at': tp_new.updated_at
                })
                return Response({'data': serializer_out.data}, status=status.HTTP_201_CREATED)

        except Club.DoesNotExist:
            return Response({"error": "Club not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
