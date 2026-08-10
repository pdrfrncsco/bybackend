from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404

from players.models import Player, PlayerFootballProfile
from players.serializers.player_football_profile import PlayerFootballProfileSerializer


class PlayerFootballProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve (public) and update (staff) player's football profile."""

    serializer_class = PlayerFootballProfileSerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "POST", "DELETE"):
            return [IsAdminUser()]
        return [AllowAny()]

    def get_object(self):
        slug = self.kwargs.get("slug")
        player = get_object_or_404(Player, slug=slug)
        # Ensure a FootballProfile exists for the player — do not create automatically on GET
        profile = getattr(player, "football_profile", None)
        if not profile:
            # create a minimal profile populated from legacy player fields where present
            profile = PlayerFootballProfile.objects.create(
                player=player,
                primary_position=getattr(player, "primary_position", None),
                shirt_number=getattr(player, "shirt_number", None),
                height_cm=getattr(player, "height_cm", None),
                weight_kg=getattr(player, "weight_kg", None),
                foot=getattr(player, "foot", None),
                total_matches=getattr(player, "total_matches", 0),
                total_goals=getattr(player, "total_goals", 0),
                total_assists=getattr(player, "total_assists", 0),
            )
        return profile
