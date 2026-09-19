from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model

from accounts.admin import (
    CustomUserAdmin,
    TenantMembershipInline,
    UserClubMemberInline,
    PlayerProfileInline,
)
from accounts.models import TenantMembership
from core.models import Tenant
from clubs.models import Club, ClubMember
from clubs.admin import ClubAdmin, ClubMemberInline
from players.models import Player
from players.admin import PlayerAdmin

User = get_user_model()


class AdminMembershipAndProfileIntegrationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()

        self.admin_user = User.objects.create_superuser(
            email="superadmin@bolayetu.com",
            username="superadmin",
            password="AdminPass123!",
        )

        self.tenant = Tenant.objects.create(
            name="Federação Angolana",
            slug="faf",
            status=Tenant.TenantStatus.ACTIVE,
            is_public=True,
        )

        self.club = Club.objects.create(
            tenant=self.tenant,
            name="1º de Agosto",
            slug="1-de-agosto",
            status="active",
            is_public=True,
        )

        self.user = User.objects.create_user(
            email="atleta@bolayetu.com",
            username="atleta_mestre",
            first_name="Carlos",
            last_name="Alves",
            password="UserPass123!",
        )

    def test_custom_user_admin_inlines_configured(self):
        user_admin = CustomUserAdmin(User, self.site)
        inline_classes = [inline.__class__ if not isinstance(inline, type) else inline for inline in user_admin.inlines]
        self.assertIn(TenantMembershipInline, inline_classes)
        self.assertIn(UserClubMemberInline, inline_classes)
        self.assertIn(PlayerProfileInline, inline_classes)

    def test_club_admin_inlines_configured(self):
        club_admin = ClubAdmin(Club, self.site)
        inline_classes = [inline.__class__ if not isinstance(inline, type) else inline for inline in club_admin.inlines]
        self.assertIn(ClubMemberInline, inline_classes)

    def test_user_admin_display_methods(self):
        user_admin = CustomUserAdmin(User, self.site)

        # Before linking
        self.assertEqual(user_admin.tenants_display(self.user), "—")
        self.assertEqual(user_admin.clubs_display(self.user), "—")
        self.assertIn("—", user_admin.player_display(self.user))

        # 1. Link to Tenant
        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role="admin",
            is_active=True,
        )
        self.assertIn("Federação Angolana", user_admin.tenants_display(self.user))

        # 2. Link to Club
        ClubMember.objects.create(
            user=self.user,
            club=self.club,
            role="coach",
            is_active=True,
        )
        self.assertIn("1º de Agosto", user_admin.clubs_display(self.user))

        # 3. Link to Player
        player = Player.objects.create(
            user=self.user,
            first_name="Carlos",
            last_name="Alves",
            primary_position="st",
            status="active",
        )
        player_display = user_admin.player_display(self.user)
        self.assertIn("Carlos Alves", player_display)
        self.assertIn(f"/admin/players/player/{player.pk}/change/", player_display)

    def test_player_admin_user_links_and_autocomplete(self):
        player_admin = PlayerAdmin(Player, self.site)
        self.assertIn("user", player_admin.autocomplete_fields)

        # Create unlinked player
        player = Player.objects.create(
            first_name="Zito",
            last_name="Luvumbo",
            primary_position="rw",
            status="active",
        )
        self.assertIn("—", player_admin.user_account_link(player))
        self.assertIn("Nenhum usuário", player_admin.user_link(player))

        # Link player to user
        player.user = self.user
        player.save()

        account_link = player_admin.user_account_link(player)
        self.assertIn(f"/admin/accounts/user/{self.user.pk}/change/", account_link)
        self.assertIn("Carlos Alves", account_link)

        user_link = player_admin.user_link(player)
        self.assertIn(f"/admin/accounts/user/{self.user.pk}/change/", user_link)
        self.assertIn(self.user.email, user_link)
