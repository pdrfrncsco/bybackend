"""
BOLAYETU — Torneios Service Layer
Skills: BOLAYETU_ARCHITECTURE, BOLAYETU_BACKEND_SKILL, BOLAYETU_MULTITENANT_SKILL
"""

from datetime import datetime, timedelta, time
from rest_framework.exceptions import ValidationError

from common.base import BaseService
from .models import Tournament, TournamentGroup
from clubs.models import Club, ClubHistory
from partidas.models import Match


class TournamentService(BaseService):
    """
    Service layer for mutating Tournament and TournamentGroup.
    """

    @BaseService.atomic
    def create_tournament(self, *, data: dict) -> Tournament:
        """
        Creates a new tournament under the current tenant context.
        """
        self._assert_tenant()
        
        tournament = Tournament(tenant=self.tenant)
        for field, value in data.items():
            if hasattr(tournament, field) and field not in ['id', 'tenant', 'clubs', 'created_at', 'updated_at']:
                setattr(tournament, field, value)
                
        tournament.full_clean()
        tournament.save()
        
        if 'clubs' in data:
            tournament.clubs.set(data['clubs'])
            
        return tournament

    @BaseService.atomic
    def update_tournament(self, *, tournament: Tournament, data: dict) -> Tournament:
        """
        Updates an existing tournament.
        """
        self._assert_tenant()
        if tournament.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot edit a tournament of another tenant.")

        for field, value in data.items():
            if hasattr(tournament, field) and field not in ['id', 'tenant', 'clubs', 'created_at', 'updated_at']:
                setattr(tournament, field, value)

        tournament.full_clean()
        tournament.save()

        if 'clubs' in data:
            tournament.clubs.set(data['clubs'])

        return tournament

    @BaseService.atomic
    def delete_tournament(self, *, tournament: Tournament) -> None:
        """
        Deletes a tournament.
        """
        self._assert_tenant()
        if tournament.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot delete a tournament of another tenant.")
            
        tournament.delete()

    @BaseService.atomic
    def add_clubs_to_tournament(self, *, tournament: Tournament, club_ids: list[str]) -> int:
        """
        Adds multiple clubs to a tournament.
        """
        self._assert_tenant()
        if tournament.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot alter clubs in a tournament of another tenant.")

        clubs = Club.objects.filter(id__in=club_ids, tenant=self.tenant)
        tournament.clubs.add(*clubs)
        return clubs.count()

    @BaseService.atomic
    def remove_clubs_from_tournament(self, *, tournament: Tournament, club_ids: list[str]) -> int:
        """
        Removes multiple clubs from a tournament.
        """
        self._assert_tenant()
        if tournament.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot alter clubs in a tournament of another tenant.")

        clubs = Club.objects.filter(id__in=club_ids, tenant=self.tenant)
        tournament.clubs.remove(*clubs)
        return clubs.count()

    @BaseService.atomic
    def set_tournament_champions(self, *, tournament: Tournament, champion_id: str = None, runner_up_id: str = None) -> Tournament:
        """
        Sets the champion and runner-up of the tournament, and updates club histories.
        """
        self._assert_tenant()
        if tournament.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot configure champions in a tournament of another tenant.")

        if champion_id and runner_up_id and str(champion_id) == str(runner_up_id):
            raise ValidationError("Campeão e vice-campeão não podem ser o mesmo clube.")

        clubs_qs = Club.objects.filter(tournaments=tournament, tenant=self.tenant)
        
        champion_club = None
        runner_up_club = None

        if champion_id:
            try:
                champion_club = clubs_qs.get(id=champion_id)
            except Club.DoesNotExist:
                raise ValidationError("Clube campeão inválido para este torneio.")

        if runner_up_id:
            try:
                runner_up_club = clubs_qs.get(id=runner_up_id)
            except Club.DoesNotExist:
                raise ValidationError("Clube vice-campeão inválido para este torneio.")

        tournament.champion_club = champion_club
        tournament.runner_up_club = runner_up_club
        tournament.save()

        if champion_club:
            ClubHistory.objects.update_or_create(
                club=champion_club,
                season=tournament.season,
                tournament_name=tournament.name,
                defaults={
                    'placement': '1º Lugar',
                    'is_trophy': True,
                },
            )

        if runner_up_club:
            ClubHistory.objects.update_or_create(
                club=runner_up_club,
                season=tournament.season,
                tournament_name=tournament.name,
                defaults={
                    'placement': '2º Lugar',
                    'is_trophy': False,
                },
            )

        return tournament

    @BaseService.atomic
    def set_tournament_groups(self, *, tournament: Tournament, groups_data: list[dict]) -> None:
        """
        Sets up the groups for a group-stage tournament.
        Deletes existing groups and creates new ones.
        """
        self._assert_tenant()
        if tournament.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot configure groups in a tournament of another tenant.")

        # Remove existing groups
        TournamentGroup.objects.filter(tournament=tournament).delete()

        for group_data in groups_data:
            name = group_data.get('name')
            club_ids = group_data.get('club_ids', [])
            if not name or not club_ids:
                continue

            group = TournamentGroup.objects.create(
                tenant=self.tenant,
                tournament=tournament,
                name=name
            )
            clubs = Club.objects.filter(id__in=club_ids, tenant=self.tenant)
            group.clubs.set(clubs)

    @BaseService.atomic
    def generate_tournament_schedule(self, *, tournament: Tournament, start_date_str: str = None, interval_days: int = 7) -> list[str]:
        """
        Generates matches for the tournament using a Round Robin algorithm.
        Clears existing matches.
        """
        self._assert_tenant()
        if tournament.tenant != self.tenant:
            from common.exceptions import PermissionDeniedException
            raise PermissionDeniedException("You cannot generate schedule in a tournament of another tenant.")

        start_date = tournament.start_date
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Clear existing matches
        Match.objects.filter(tournament=tournament).delete()

        matches_created = []

        if tournament.type == 'Groups':
            groups = tournament.groups.all()
            if groups.exists():
                for group in groups:
                    group_clubs = list(group.clubs.all())
                    matches_created.extend(self._generate_round_robin(group_clubs, start_date, interval_days, tournament))
            else:
                clubs = list(tournament.clubs.all())
                if len(clubs) < 2:
                    raise ValidationError("São necessários pelo menos 2 clubs para gerar o calendário.")
                matches_created.extend(self._generate_round_robin(clubs, start_date, interval_days, tournament))
        else:
            clubs = list(tournament.clubs.all())
            if len(clubs) < 2:
                raise ValidationError("São necessários pelo menos 2 clubs para gerar o calendário.")
            matches_created.extend(self._generate_round_robin(clubs, start_date, interval_days, tournament))

        return matches_created

    def _generate_round_robin(self, clubs: list, start_date, interval_days: int, tournament: Tournament) -> list:
        """
        Helper method to run round robin scheduling.
        """
        if len(clubs) < 2:
            return []

        # Round Robin Logic
        if len(clubs) % 2 != 0:
            # Dummy representing bye
            clubs.append(None)

        n = len(clubs)
        rounds = n - 1
        matches_per_round = n // 2

        matches_created = []
        current_date = start_date

        for r in range(rounds):
            round_name = f"Jornada {r + 1}"

            for i in range(matches_per_round):
                home = clubs[i]
                away = clubs[n - 1 - i]

                if home and away:
                    # Swap home/away based on round to balance
                    if r % 2 == 1:
                        home, away = away, home

                    # Create datetime from date (default 15:00)
                    match_datetime = datetime.combine(current_date, time(15, 0))

                    match = Match.objects.create(
                        tenant=self.tenant,
                        tournament=tournament,
                        home_team=home,
                        away_team=away,
                        date=match_datetime,
                        round=round_name,
                        status='scheduled'
                    )
                    matches_created.append(str(match.id))

            # Rotate clubs (keep index 0 fixed)
            clubs = [clubs[0]] + [clubs[-1]] + clubs[1:-1]
            current_date += timedelta(days=interval_days)

        return matches_created
