from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory

from media_assets.constants import AssetCategory, OwnerType
from media_assets.models import MediaAsset, MediaUsage
from players.models import Player
from players.serializers import PlayerSerializer, PlayerDetailSerializer
from players.services import PlayerService

User = get_user_model()


class PlayerAvatarSerializationTestCase(TestCase):
    def setUp(self):
        self.rf = APIRequestFactory()
        self.user = User.objects.create_user(
            email="avatar-test@example.com",
            password="SecurePass123!",
        )
        self.player = Player.objects.create(
            user=self.user,
            first_name="Pedro",
            last_name="Francisco",
            slug="pedro-francisco",
            date_of_birth=date(1995, 5, 20),
            nationality="AO",
            primary_position="st",
            status="active",
        )
        self.asset = MediaAsset.objects.create(
            name="Pedro Francisco Avatar",
            original_filename="avatar.png",
            object_key="tenant/test/player/avatar/avatar.png",
            asset_type="image",
            category="avatar",
            mime_type="image/png",
            extension="png",
            size_bytes=2048,
            cdn_url="/media/tenant/test/player/avatar/avatar.png",
        )

    def test_avatar_from_media_usage(self):
        """Player with active MediaUsage(role='avatar') resolves in PlayerSerializer."""
        MediaUsage.objects.create(
            asset=self.asset,
            owner_type=OwnerType.PLAYER,
            owner_id=self.player.id,
            role=AssetCategory.AVATAR,
            is_active=True,
        )

        serializer = PlayerSerializer(self.player)
        self.assertEqual(serializer.data["avatar"], "/media/tenant/test/player/avatar/avatar.png")
        self.assertEqual(serializer.data["profile_photo_url"], "/media/tenant/test/player/avatar/avatar.png")

        detail_serializer = PlayerDetailSerializer(self.player)
        self.assertEqual(detail_serializer.data["avatar"], "/media/tenant/test/player/avatar/avatar.png")
        self.assertEqual(detail_serializer.data["profile_photo_url"], "/media/tenant/test/player/avatar/avatar.png")

    def test_avatar_with_request_context_resolves_absolute_url(self):
        """When request is provided in context, avatar URL is fully qualified."""
        MediaUsage.objects.create(
            asset=self.asset,
            owner_type=OwnerType.PLAYER,
            owner_id=self.player.id,
            role=AssetCategory.AVATAR,
            is_active=True,
        )

        request = self.rf.get("/api/v1/players/pedro-francisco/")
        serializer = PlayerSerializer(self.player, context={"request": request})
        self.assertTrue(serializer.data["avatar"].startswith("http://testserver/media/"))
        self.assertEqual(
            serializer.data["avatar"],
            "http://testserver/media/tenant/test/player/avatar/avatar.png"
        )
        self.assertEqual(
            serializer.data["profile_photo_url"],
            "http://testserver/media/tenant/test/player/avatar/avatar.png"
        )

    def test_avatar_from_profile_photo_foreign_key(self):
        """Player with profile_photo FK linked resolves properly."""
        self.player.profile_photo = self.asset
        self.player.save(update_fields=["profile_photo"])

        serializer = PlayerSerializer(self.player)
        self.assertEqual(serializer.data["avatar"], "/media/tenant/test/player/avatar/avatar.png")
        self.assertEqual(serializer.data["profile_photo_url"], "/media/tenant/test/player/avatar/avatar.png")

    def test_avatar_from_legacy_field_fallback(self):
        """When no DAM asset is linked, fallback to legacy avatar URL field."""
        self.player.avatar = "https://cdn.example.com/legacy.jpg"
        self.player.save(update_fields=["avatar"])

        serializer = PlayerSerializer(self.player)
        self.assertEqual(serializer.data["avatar"], "https://cdn.example.com/legacy.jpg")
        self.assertEqual(serializer.data["profile_photo_url"], "https://cdn.example.com/legacy.jpg")

    def test_avatar_none_when_unconfigured(self):
        """Player with no avatar, no profile_photo, and no MediaUsage returns None."""
        serializer = PlayerSerializer(self.player)
        self.assertIsNone(serializer.data["avatar"])
        self.assertIsNone(serializer.data["profile_photo_url"])

    def test_player_update_links_profile_photo_from_url_or_path(self):
        """Updating player avatar with absolute URL correctly resolves and links MediaAsset."""
        PlayerService.update_player(
            self.player,
            avatar="http://localhost:8000/media/tenant/test/player/avatar/avatar.png"
        )
        self.player.refresh_from_db()
        self.assertEqual(self.player.profile_photo_id, self.asset.id)
