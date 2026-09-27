"""
BOLAYETU — Fans App Unit & API Tests (APITestCase)
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import TenantMembership
from clubs.models import Club, ClubMember
from competitions.models import Competition, Match
from core.models import Tenant
from players.models import Player
from fans.models import (
    FanProfile,
    FanFollow,
    MatchPrediction,
    FollowTargetType,
    PredictionStatus,
    FeedPost,
    FeedPostLike,
    FeedPostComment,
    PostAuthorType,
    PostCategory,
)
from fans.services import MatchPredictionService, FeedPostService

User = get_user_model()


class FansBaseTestCase(APITestCase):
    def setUp(self):
        self.fan_user = User.objects.create_user(
            email="adepto@boayetu.ao",
            username="adepto_fiel",
            first_name="João",
            last_name="Lourenço",
            password="password123",
            profile_type="fan",
        )
        self.club_manager_user = User.objects.create_user(
            email="admin@petro.ao",
            username="petro_admin",
            first_name="Carlos",
            last_name="Manuel",
            password="password123",
            profile_type="club",
        )
        self.player_user = User.objects.create_user(
            email="tiagol@boayetu.ao",
            username="tiago_azul",
            first_name="Tiago",
            last_name="Azul",
            password="password123",
            profile_type="player",
        )
        self.tenant = Tenant.objects.create(
            name="Federação Angolana de Futebol",
            slug="faf",
            type="federation",
            subdomain="faf",
        )
        self.club = Club.objects.create(
            name="Petro Atlético de Luanda",
            slug="petro-atletico",
            tenant=self.tenant,
        )
        self.club_away = Club.objects.create(
            name="1º de Agosto",
            slug="1-de-agosto",
            tenant=self.tenant,
        )
        ClubMember.objects.create(
            club=self.club,
            user=self.club_manager_user,
            role="club_admin",
            is_active=True,
        )
        self.player = Player.objects.create(
            user=self.player_user,
            first_name="Tiago",
            last_name="Azul",
            primary_position="Forward",
        )
        self.competition = Competition.objects.create(
            name="Girabola 2026/27",
            slug="girabola-26-27",
            tenant=self.tenant,
            season="2026/2027",
        )
        self.match = Match.objects.create(
            competition=self.competition,
            tenant=self.tenant,
            home_club=self.club,
            away_club=self.club_away,
            match_date=timezone.now(),
            round_number=1,
            round_name="Jornada 1",
            status="scheduled",
        )


class TestFanProfileAPI(FansBaseTestCase):
    def test_get_my_profile_auto_creates(self):
        self.client.force_authenticate(user=self.fan_user)
        url = reverse("fans:fan-profile-me")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "adepto@boayetu.ao")
        self.assertEqual(response.data["points"], 0)
        self.assertTrue(FanProfile.objects.filter(user=self.fan_user).exists())

    def test_update_my_profile_preferences(self):
        self.client.force_authenticate(user=self.fan_user)
        url = reverse("fans:fan-profile-me")
        payload = {
            "favorite_club": str(self.club.id),
            "bio": "Adepto ferrenho do Petro!",
            "location": "Luanda",
            "notification_goals": True,
        }
        response = self.client.patch(url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bio"], "Adepto ferrenho do Petro!")
        self.assertEqual(str(response.data["favorite_club"]), str(self.club.id))
        self.assertEqual(response.data["favorite_club_name"], "Petro Atlético de Luanda")


class TestFanFollowAPI(FansBaseTestCase):
    def test_toggle_follow_club(self):
        self.client.force_authenticate(user=self.fan_user)
        url = reverse("fans:fan-toggle-follow")

        # 1. Follow club
        response = self.client.post(
            url,
            data={"target_type": "club", "target_id": str(self.club.id)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_following"])
        self.assertTrue(FanFollow.objects.filter(user=self.fan_user, club=self.club).exists())

        # 2. List follows
        list_url = reverse("fans:fan-follows-list")
        list_resp = self.client.get(list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_resp.data), 1)
        self.assertEqual(list_resp.data[0]["name"], "Petro Atlético de Luanda")

        # 3. Unfollow club
        response_unfollow = self.client.post(
            url,
            data={"target_type": "club", "target_id": str(self.club.id)},
            format="json",
        )
        self.assertEqual(response_unfollow.status_code, status.HTTP_200_OK)
        self.assertFalse(response_unfollow.data["is_following"])
        self.assertFalse(FanFollow.objects.filter(user=self.fan_user, club=self.club).exists())


class TestMatchPrediction(FansBaseTestCase):
    def test_submit_prediction_and_evaluation(self):
        self.client.force_authenticate(user=self.fan_user)
        url = reverse("fans:fan-predictions")

        # Submit prediction: Petro 2 - 1 1º de Agosto
        payload = {
            "match_id": str(self.match.id),
            "predicted_home_score": 2,
            "predicted_away_score": 1,
        }
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["predicted_home_score"], 2)
        self.assertEqual(response.data["predicted_away_score"], 1)
        self.assertEqual(response.data["status"], "pending")

        # Simulate match finish with EXACT score (2 - 1)
        self.match.home_score = 2
        self.match.away_score = 1
        self.match.status = "finished"
        self.match.save()

        evaluated = MatchPredictionService.evaluate_match_predictions(self.match)
        self.assertEqual(evaluated, 1)

        pred = MatchPrediction.objects.get(user=self.fan_user, match=self.match)
        self.assertEqual(pred.status, PredictionStatus.EVALUATED)
        self.assertEqual(pred.points_awarded, 50)

        # Check FanProfile points updated
        profile = FanProfile.objects.get(user=self.fan_user)
        self.assertEqual(profile.points, 50)
        self.assertEqual(profile.correct_predictions_count, 1)

    def test_leaderboard_ranking(self):
        other_user = User.objects.create_user(
            email="superfan@boayetu.ao",
            username="super_fan",
            password="password123",
        )
        FanProfile.objects.create(user=self.fan_user, points=100)
        FanProfile.objects.create(user=other_user, points=250)

        url = reverse("fans:fan-leaderboard")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["username"], "super_fan")
        self.assertEqual(response.data[0]["rank"], 1)
        self.assertEqual(response.data[1]["username"], "adepto_fiel")
        self.assertEqual(response.data[1]["rank"], 2)


class TestFeedPublishingAndSocialAPI(FansBaseTestCase):
    def test_club_publishes_post_successfully(self):
        self.client.force_authenticate(user=self.club_manager_user)
        url = reverse("fans:feed-posts")

        payload = {
            "author_type": PostAuthorType.CLUB,
            "category": PostCategory.MATCHDAY,
            "title": "Convocatória Oficial para o Dérbi",
            "content": "Confira a lista dos 20 convocados pelo mister para o jogo de amanhã!",
            "club_id": str(self.club.id),
        }
        response = self.client.post(url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Convocatória Oficial para o Dérbi")
        self.assertEqual(response.data["author_name"], "Petro Atlético de Luanda")
        self.assertEqual(response.data["likes_count"], 0)
        self.assertTrue(FeedPost.objects.filter(club=self.club).exists())

    def test_player_publishes_post_successfully(self):
        self.client.force_authenticate(user=self.player_user)
        url = reverse("fans:feed-posts")

        payload = {
            "author_type": PostAuthorType.PLAYER,
            "category": PostCategory.TRAINING,
            "title": "Preparação Forte",
            "content": "Treino concluído com intensidade máxima antes do grande jogo!",
            "player_id": str(self.player.id),
        }
        response = self.client.post(url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author_name"], "Tiago Azul")
        self.assertTrue(FeedPost.objects.filter(player=self.player).exists())

    def test_fan_cannot_publish_as_unauthorized_club(self):
        self.client.force_authenticate(user=self.fan_user)
        url = reverse("fans:feed-posts")

        payload = {
            "author_type": PostAuthorType.CLUB,
            "title": "Tentativa não autorizada",
            "content": "Conteúdo falso",
            "club_id": str(self.club.id),
        }
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_fan_can_like_and_comment_on_post(self):
        # 1. Create post
        post = FeedPostService.create_post(
            user=self.club_manager_user,
            author_type=PostAuthorType.CLUB,
            title="Comunicado Oficial",
            content="Grande vitória no clássico!",
            club_id=self.club.id,
        )

        # 2. Fan likes post
        self.client.force_authenticate(user=self.fan_user)
        like_url = reverse("fans:feed-post-like", kwargs={"post_id": post.id})
        like_resp = self.client.post(like_url)

        self.assertEqual(like_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(like_resp.data["is_liked"])
        self.assertEqual(like_resp.data["likes_count"], 1)
        self.assertTrue(FeedPostLike.objects.filter(user=self.fan_user, post=post).exists())

        # 3. Fan comments on post
        comment_url = reverse("fans:feed-post-comments", kwargs={"post_id": post.id})
        comm_resp = self.client.post(comment_url, data={"content": "Orgulho imenso nesta equipa! Força!"}, format="json")

        self.assertEqual(comm_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(comm_resp.data["content"], "Orgulho imenso nesta equipa! Força!")
        self.assertEqual(comm_resp.data["author_name"], "João Lourenço")

        post.refresh_from_db()
        self.assertEqual(post.comments_count, 1)
