from datetime import datetime, timezone
from django.test import TestCase

from core.models import Tenant
from clubs.models import Club
from players.models import Player
from competitions.models import (
    Competition, CompetitionRegistration, Match, MatchEvent, MatchLineup,
    PlayerSuspension, MatchReport
)
from competitions.services.lineup_service import (
    LineupService, LineupValidationError, LineupConfig
)
from competitions.services.competition_format_service import CompetitionFormatService
from competitions.services.match_service import MatchService
from competitions.services.match_event_service import (
    MatchEventService, InvalidMatchEventData
)


class AuditEnhancementsTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Fed Teste", slug="fed-teste")
        self.competition = Competition.objects.create(
            tenant=self.tenant,
            name="Taça de Angola",
            competition_type="cup",
            season="2025/26",
        )
        self.club1 = Club.objects.create(name="Petro", slug="petro", tenant=self.tenant, city="Luanda")
        self.club2 = Club.objects.create(name="1º de Agosto", slug="pri-agosto", tenant=self.tenant, city="Luanda")
        
        # Register clubs in competition
        CompetitionRegistration.objects.create(tenant=self.tenant, competition=self.competition, club=self.club1)
        CompetitionRegistration.objects.create(tenant=self.tenant, competition=self.competition, club=self.club2)

        self.match = Match.objects.create(
            tenant=self.tenant,
            competition=self.competition,
            home_club=self.club1,
            away_club=self.club2,
            match_date=datetime.now(timezone.utc),
            round_number=1,
            round_name="Final",
            phase="knockout",
        )

        self.players = [
            Player.objects.create(
                first_name=f"Jogador{i}",
                last_name=f"Sobrenome{i}",
                primary_position="gk" if i == 1 else ("cb" if i <= 5 else ("cm" if i <= 8 else "st")),
            )
            for i in range(1, 19)
        ]

    def test_lineup_requires_exactly_one_goalkeeper(self):
        """Lineup validation rejects starting XI with zero or multiple goalkeepers."""
        # Zero goalkeepers
        players_no_gk = [
            {"player_id": str(self.players[i].id), "status": "starter", "position": "cb", "shirt_number": i}
            for i in range(11)
        ]
        with self.assertRaises(LineupValidationError) as ctx:
            LineupService._validate_lineup(players_no_gk, formation="4-3-3")
        self.assertIn("guarda-redes", str(ctx.exception).lower())

        # Two goalkeepers
        players_two_gk = [
            {"player_id": str(self.players[i].id), "status": "starter", "position": "gk" if i < 2 else "cb", "shirt_number": i + 1}
            for i in range(11)
        ]
        with self.assertRaises(LineupValidationError) as ctx:
            LineupService._validate_lineup(players_two_gk, formation="4-3-3")
        self.assertIn("guarda-redes", str(ctx.exception).lower())

    def test_lineup_formation_coherence(self):
        """Lineup validation enforces position distribution matching formation."""
        # 4-3-3 requires 4 DEF, 3 MID, 3 FWD + 1 GK
        valid_433 = [
            {"player_id": str(self.players[0].id), "status": "starter", "position": "gk", "shirt_number": 1},
            {"player_id": str(self.players[1].id), "status": "starter", "position": "lb", "shirt_number": 2},
            {"player_id": str(self.players[2].id), "status": "starter", "position": "cb", "shirt_number": 3},
            {"player_id": str(self.players[3].id), "status": "starter", "position": "cb", "shirt_number": 4},
            {"player_id": str(self.players[4].id), "status": "starter", "position": "rb", "shirt_number": 5},
            {"player_id": str(self.players[5].id), "status": "starter", "position": "cdm", "shirt_number": 6},
            {"player_id": str(self.players[6].id), "status": "starter", "position": "cm", "shirt_number": 7},
            {"player_id": str(self.players[7].id), "status": "starter", "position": "cam", "shirt_number": 8},
            {"player_id": str(self.players[8].id), "status": "starter", "position": "lw", "shirt_number": 9},
            {"player_id": str(self.players[9].id), "status": "starter", "position": "st", "shirt_number": 10},
            {"player_id": str(self.players[10].id), "status": "starter", "position": "rw", "shirt_number": 11},
        ]
        # Should succeed without exception
        LineupService._validate_lineup(valid_433, formation="4-3-3")

        # Incoherent formation: only 3 defenders with 4-3-3
        incoherent_433 = [dict(p) for p in valid_433]
        incoherent_433[4]["position"] = "st"  # changed DEF to FWD
        with self.assertRaises(LineupValidationError) as ctx:
            LineupService._validate_lineup(incoherent_433, formation="4-3-3")
        self.assertIn("defesas", str(ctx.exception).lower())

    def test_knockout_penalty_shootout_winner(self):
        """CompetitionFormatService._winner_from_match recognizes penalty score in tie."""
        self.match.home_score = 1
        self.match.away_score = 1
        self.match.home_penalty_score = 4
        self.match.away_penalty_score = 3
        self.match.save()

        winner = CompetitionFormatService._winner_from_match(self.match)
        self.assertEqual(winner, self.club1)

        self.match.home_penalty_score = 2
        self.match.away_penalty_score = 5
        self.match.save()

        winner2 = CompetitionFormatService._winner_from_match(self.match)
        self.assertEqual(winner2, self.club2)

    def test_match_schedule_protection_against_deletion(self):
        """Regenerating schedule or draw fails if matches are finished or have events."""
        self.match.status = Match.MatchStatus.FINISHED
        self.match.save()

        with self.assertRaises(ValueError) as ctx:
            CompetitionFormatService.generate_draw(
                tenant=self.tenant,
                competition=self.competition,
                start_date=datetime.now(timezone.utc),
            )
        self.assertIn("andamento", str(ctx.exception).lower())

        with self.assertRaises(ValueError) as ctx2:
            MatchService.generate_round_robin_schedule(
                tenant=self.tenant,
                competition=self.competition,
                start_date=datetime.now(timezone.utc),
            )
        self.assertIn("andamento", str(ctx2.exception).lower())

    def test_match_event_extra_time_minutes_and_fair_play_suspension(self):
        """Match event accepts minutes up to 135 and creates automatic suspension on red card."""
        player = self.players[0]

        # Over 135 fails
        with self.assertRaises(InvalidMatchEventData):
            MatchEventService.add_event(
                tenant=self.tenant,
                match=self.match,
                club=self.club1,
                event_type=MatchEvent.EventType.RED_CARD,
                minute=136,
                player=player,
            )

        # Minute 122 (extra time stoppage time) succeeds
        event = MatchEventService.add_event(
            tenant=self.tenant,
            match=self.match,
            club=self.club1,
            event_type=MatchEvent.EventType.RED_CARD,
            minute=122,
            player=player,
        )
        self.assertIsNotNone(event)

        # Verify automatic suspension was created
        suspension = PlayerSuspension.objects.filter(
            tenant=self.tenant,
            player=player,
            competition=self.competition,
            trigger_event=event,
        ).first()
        self.assertIsNotNone(suspension)
        self.assertEqual(suspension.suspension_type, PlayerSuspension.SuspensionType.RED_CARD)

        # Removing event deletes/cleans up suspension
        MatchEventService.remove_event(tenant=self.tenant, event_id=str(event.id))
        self.assertFalse(
            PlayerSuspension.objects.filter(trigger_event=event).exists()
        )

    def test_match_substitution_minutes_tracked_in_lineup(self):
        """Substitution in/out events update substituted minutes on MatchLineup."""
        p_on = self.players[1]
        p_off = self.players[2]

        lineup_on = MatchLineup.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club1,
            player=p_on,
            status=MatchLineup.LineupStatus.SUBSTITUTE,
            position="cm",
            shirt_number=14,
        )
        lineup_off = MatchLineup.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club1,
            player=p_off,
            status=MatchLineup.LineupStatus.STARTER,
            position="cm",
            shirt_number=8,
        )

        sub_event = MatchEventService.add_event(
            tenant=self.tenant,
            match=self.match,
            club=self.club1,
            event_type=MatchEvent.EventType.SUBSTITUTION_IN,
            minute=65,
            player=p_on,
            player_off=p_off,
        )

        lineup_on.refresh_from_db()
        lineup_off.refresh_from_db()

        self.assertEqual(lineup_on.substituted_in_minute, 65)
        self.assertEqual(lineup_off.substituted_out_minute, 65)

        # Removing the substitution event clears the minutes
        MatchEventService.remove_event(tenant=self.tenant, event_id=str(sub_event.id))
        lineup_on.refresh_from_db()
        lineup_off.refresh_from_db()
        self.assertIsNone(lineup_on.substituted_in_minute)
        self.assertIsNone(lineup_off.substituted_out_minute)
