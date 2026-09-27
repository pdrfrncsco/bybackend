"""
BOLAYETU — Fans App Unit & API Tests
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from clubs.models import Club
from competitions.models import Competition, Match
from core.models import Tenant
from fans.models import FanProfile, FanFollow, MatchPrediction, FollowTargetType, PredictionStatus
from fans.services import MatchPredictionService

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def fan_user(db):
    return User.objects.create_user(
        email="adepto@boayetu.ao",
        username="adepto_fiel",
        first_name="João",
        last_name="Lourenço",
        password="password123",
        profile_type="fan",
    )


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        name="Federação Angolana de Futebol",
        slug="faf",
        type="federation",
        subdomain="faf",
    )


@pytest.fixture
def club(db, tenant):
    return Club.objects.create(
        name="Petro Atlético de Luanda",
        slug="petro-atletico",
        tenant=tenant,
    )


@pytest.fixture
def club_away(db, tenant):
    return Club.objects.create(
        name="1º de Agosto",
        slug="1-de-agosto",
        tenant=tenant,
    )


@pytest.fixture
def competition(db, tenant):
    return Competition.objects.create(
        name="Girabola 2026/27",
        slug="girabola-26-27",
        tenant=tenant,
        season="2026/2027",
    )


@pytest.fixture
def match(db, competition, tenant, club, club_away):
    return Match.objects.create(
        competition=competition,
        tenant=tenant,
        home_club=club,
        away_club=club_away,
        match_date=timezone.now(),
        round_number=1,
        round_name="Jornada 1",
        status="scheduled",
    )


@pytest.mark.django_db
class TestFanProfileAPI:
    def test_get_my_profile_auto_creates(self, api_client, fan_user):
        api_client.force_authenticate(user=fan_user)
        url = reverse("fans:fan-profile-me")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "adepto@boayetu.ao"
        assert response.data["points"] == 0
        assert FanProfile.objects.filter(user=fan_user).exists()

    def test_update_my_profile_preferences(self, api_client, fan_user, club):
        api_client.force_authenticate(user=fan_user)
        url = reverse("fans:fan-profile-me")
        payload = {
            "favorite_club": str(club.id),
            "bio": "Adepto ferrenho do Petro!",
            "location": "Luanda",
            "notification_goals": True,
        }
        response = api_client.patch(url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["bio"] == "Adepto ferrenho do Petro!"
        assert str(response.data["favorite_club"]) == str(club.id)
        assert response.data["favorite_club_name"] == "Petro Atlético de Luanda"


@pytest.mark.django_db
class TestFanFollowAPI:
    def test_toggle_follow_club(self, api_client, fan_user, club):
        api_client.force_authenticate(user=fan_user)
        url = reverse("fans:fan-toggle-follow")

        # 1. Follow club
        response = api_client.post(
            url,
            data={"target_type": "club", "target_id": str(club.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_following"] is True
        assert FanFollow.objects.filter(user=fan_user, club=club).exists()

        # 2. List follows
        list_url = reverse("fans:fan-follows-list")
        list_resp = api_client.get(list_url)
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.data) == 1
        assert list_resp.data[0]["name"] == "Petro Atlético de Luanda"

        # 3. Unfollow club
        response_unfollow = api_client.post(
            url,
            data={"target_type": "club", "target_id": str(club.id)},
            format="json",
        )
        assert response_unfollow.status_code == status.HTTP_200_OK
        assert response_unfollow.data["is_following"] is False
        assert not FanFollow.objects.filter(user=fan_user, club=club).exists()


@pytest.mark.django_db
class TestMatchPrediction:
    def test_submit_prediction_and_evaluation(self, api_client, fan_user, match):
        api_client.force_authenticate(user=fan_user)
        url = reverse("fans:fan-predictions")

        # Submit prediction: Petro 2 - 1 1º de Agosto
        payload = {
            "match_id": str(match.id),
            "predicted_home_score": 2,
            "predicted_away_score": 1,
        }
        response = api_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["predicted_home_score"] == 2
        assert response.data["predicted_away_score"] == 1
        assert response.data["status"] == "pending"

        # Simulate match finish with EXACT score (2 - 1)
        match.home_score = 2
        match.away_score = 1
        match.status = "finished"
        match.save()

        evaluated = MatchPredictionService.evaluate_match_predictions(match)
        assert evaluated == 1

        pred = MatchPrediction.objects.get(user=fan_user, match=match)
        assert pred.status == PredictionStatus.EVALUATED
        assert pred.points_awarded == 50

        # Check FanProfile points updated
        profile = FanProfile.objects.get(user=fan_user)
        assert profile.points == 50
        assert profile.correct_predictions_count == 1

    def test_leaderboard_ranking(self, api_client, fan_user):
        # Create a second user with more points
        other_user = User.objects.create_user(
            email="superfan@boayetu.ao",
            username="super_fan",
            password="password123",
        )
        FanProfile.objects.create(user=fan_user, points=100)
        FanProfile.objects.create(user=other_user, points=250)

        url = reverse("fans:fan-leaderboard")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]["username"] == "super_fan"
        assert response.data[0]["rank"] == 1
        assert response.data[1]["username"] == "adepto_fiel"
        assert response.data[1]["rank"] == 2
