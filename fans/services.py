"""
BOLAYETU — Fans App Domain Services
"""

from typing import Tuple
from uuid import UUID
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from clubs.models import Club
from players.models import Player
from competitions.models import Match, Competition
from .models import (
    FanProfile,
    FanFollow,
    MatchPrediction,
    FanMVPVote,
    FollowTargetType,
    PredictionStatus,
)

User = get_user_model()


class FanProfileService:
    """Handles fan profile creation and updates."""

    @staticmethod
    def get_or_create_profile(user) -> FanProfile:
        profile, _ = FanProfile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def update_profile(user, **data) -> FanProfile:
        profile = FanProfileService.get_or_create_profile(user)
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.save()
        return profile


class FanFollowService:
    """Handles following/unfollowing clubs, players, and competitions."""

    @staticmethod
    @transaction.atomic
    def toggle_follow(user, target_type: str, target_id: UUID) -> Tuple[FanFollow | None, bool]:
        """
        Toggles follow state.
        Returns (follow_instance, is_following_now).
        """
        if target_type == FollowTargetType.CLUB:
            club = Club.objects.filter(id=target_id).first()
            if not club:
                raise ValidationError("Clube não encontrado.")
            existing = FanFollow.objects.filter(user=user, target_type=target_type, club=club).first()
            if existing:
                existing.delete()
                return None, False
            follow = FanFollow.objects.create(user=user, target_type=target_type, club=club)
            return follow, True

        elif target_type == FollowTargetType.PLAYER:
            player = Player.objects.filter(id=target_id).first()
            if not player:
                raise ValidationError("Jogador não encontrado.")
            existing = FanFollow.objects.filter(user=user, target_type=target_type, player=player).first()
            if existing:
                existing.delete()
                return None, False
            follow = FanFollow.objects.create(user=user, target_type=target_type, player=player)
            return follow, True

        elif target_type == FollowTargetType.COMPETITION:
            comp = Competition.objects.filter(id=target_id).first()
            if not comp:
                raise ValidationError("Competição não encontrada.")
            existing = FanFollow.objects.filter(user=user, target_type=target_type, competition=comp).first()
            if existing:
                existing.delete()
                return None, False
            follow = FanFollow.objects.create(user=user, target_type=target_type, competition=comp)
            return follow, True

        raise ValidationError(f"Tipo de alvo inválido: {target_type}")


class MatchPredictionService:
    """Handles match score predictions and automatic point calculation."""

    EXACT_SCORE_POINTS = 50
    OUTCOME_POINTS = 20

    @staticmethod
    @transaction.atomic
    def submit_prediction(user, match_id: UUID, home_score: int, away_score: int) -> MatchPrediction:
        match = Match.objects.filter(id=match_id).first()
        if not match:
            raise ValidationError("Partida não encontrada.")

        # Match must not be completed
        if getattr(match, "status", None) in ["completed", "finished", "archived"]:
            raise ValidationError("Não é possível registar palpites para uma partida já terminada.")

        prediction, _ = MatchPrediction.objects.update_or_create(
            user=user,
            match=match,
            defaults={
                "predicted_home_score": home_score,
                "predicted_away_score": away_score,
                "status": PredictionStatus.PENDING,
            },
        )
        return prediction

    @staticmethod
    @transaction.atomic
    def evaluate_match_predictions(match: Match) -> int:
        """
        Evaluates all pending predictions for a finished match.
        Points:
        - 50 pts: Exact score (e.g. predicted 2-1, actual 2-1)
        - 20 pts: Correct match outcome (home win / draw / away win)
        - 0 pts: Wrong outcome
        """
        if match.home_score is None or match.away_score is None:
            return 0

        actual_home = match.home_score
        actual_away = match.away_score

        # Determine actual outcome: 'home', 'draw', 'away'
        if actual_home > actual_away:
            actual_outcome = "home"
        elif actual_home < actual_away:
            actual_outcome = "away"
        else:
            actual_outcome = "draw"

        pending_predictions = MatchPrediction.objects.filter(
            match=match,
            status=PredictionStatus.PENDING,
        ).select_related("user")

        evaluated_count = 0
        now = timezone.now()

        for pred in pending_predictions:
            points = 0
            is_exact = pred.predicted_home_score == actual_home and pred.predicted_away_score == actual_away

            if pred.predicted_home_score > pred.predicted_away_score:
                pred_outcome = "home"
            elif pred.predicted_home_score < pred.predicted_away_score:
                pred_outcome = "away"
            else:
                pred_outcome = "draw"

            if is_exact:
                points = MatchPredictionService.EXACT_SCORE_POINTS
            elif pred_outcome == actual_outcome:
                points = MatchPredictionService.OUTCOME_POINTS

            pred.points_awarded = points
            pred.status = PredictionStatus.EVALUATED
            pred.evaluated_at = now
            pred.save(update_fields=["points_awarded", "status", "evaluated_at"])

            # Update FanProfile stats
            profile = FanProfileService.get_or_create_profile(pred.user)
            profile.points += points
            profile.total_predictions_count += 1
            if points > 0:
                profile.correct_predictions_count += 1
            profile.save(update_fields=["points", "total_predictions_count", "correct_predictions_count"])

            evaluated_count += 1

        return evaluated_count


class FanMVPVoteService:
    """Handles fan voting for MVP of a match."""

    @staticmethod
    @transaction.atomic
    def cast_vote(user, match_id: UUID, player_id: UUID) -> FanMVPVote:
        match = Match.objects.filter(id=match_id).first()
        if not match:
            raise ValidationError("Partida não encontrada.")

        player = Player.objects.filter(id=player_id).first()
        if not player:
            raise ValidationError("Jogador não encontrado.")

        vote, _ = FanMVPVote.objects.update_or_create(
            user=user,
            match=match,
            defaults={"player": player},
        )
        return vote
