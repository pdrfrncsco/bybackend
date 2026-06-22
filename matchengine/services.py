from django.db.models import F, Q
from .models import MatchEvent, MatchLineupEntry
from jogadores.models import PlayerHistory
from partidas.models import Match
from treinadores.models import HistoricoTreinador

class MatchStatsService:
    @staticmethod
    def process_match_completion(match: Match):
        """
        Aggregates match stats and updates PlayerHistory and HistoricoTreinador.
        Should only be called once when match transitions to finished.
        """
        if match.stats_processed:
            print(f"Match {match.id} stats already processed. Skipping.")
            return

        if not match.tournament:
            # If no tournament, we might skip or use a default season.
            # For now, let's log and skip to avoid errors.
            print(f"Match {match.id} has no tournament. Skipping stats update.")
            return

        season = match.tournament.season

        # 1. Update Player Stats
        MatchStatsService._update_player_stats(match, season)
        
        # 2. Update Coach Stats
        MatchStatsService._update_coach_stats(match)

        # 3. Mark as processed
        match.stats_processed = True
        match.save(update_fields=['stats_processed'])

    @staticmethod
    def _update_player_stats(match: Match, season):
        # 1. Get all lineup entries
        lineup_entries = MatchLineupEntry.objects.filter(match=match).select_related('player', 'team')
        
        # 2. Get all events
        events = MatchEvent.objects.filter(match=match)

        # 3. Process each player
        for entry in lineup_entries:
            player = entry.player
            if not player:
                continue
                
            # Check if played
            played = False
            minutes = 0
            
            # Logic to calculate minutes
            # If starter, assume played full game (90) unless subbed out
            if entry.is_starter:
                played = True
                minutes = 90 # Base time
                
                # Check if subbed out
                sub_out = events.filter(type='substitution', player=player).first()
                if sub_out:
                    minutes = sub_out.minute
                
                # Check red card (optional: usually minutes count until red card)
                red_card = events.filter(type='red_card', player=player).first()
                if red_card:
                    minutes = red_card.minute

            else:
                # Check if subbed in
                sub_in = events.filter(type='substitution', secondary_player=player).first()
                if sub_in:
                    played = True
                    minutes = 90 - sub_in.minute
                    
                    # Check if subbed out (rare)
                    sub_out = events.filter(type='substitution', player=player).first()
                    if sub_out:
                        minutes = sub_out.minute - sub_in.minute
                    
                    # Check red card
                    red_card = events.filter(type='red_card', player=player).first()
                    if red_card:
                        minutes = red_card.minute - sub_in.minute

            if played:
                # Get stats from events
                goals = events.filter(type='goal', player=player, is_own_goal=False).count()
                assists = events.filter(type='goal', secondary_player=player).count()
                yellow_cards = events.filter(type='yellow_card', player=player).count()
                red_cards = events.filter(type='red_card', player=player).count()

                # Update PlayerHistory
                # We use get_or_create to ensure we have a record for this season/club
                history, created = PlayerHistory.objects.get_or_create(
                    player=player,
                    season=season,
                    club=entry.team,
                    defaults={
                        'matches': 0,
                        'goals': 0,
                        'assists': 0,
                        'minutes': 0,
                        'yellow_cards': 0,
                        'red_cards': 0
                    }
                )
                
                # Increment stats
                history.matches = F('matches') + 1
                history.goals = F('goals') + goals
                history.assists = F('assists') + assists
                history.minutes = F('minutes') + minutes
                history.yellow_cards = F('yellow_cards') + yellow_cards
                history.red_cards = F('red_cards') + red_cards
                history.save()
                
                # Force refresh to get updated values if needed later
                history.refresh_from_db()

    @staticmethod
    def _update_coach_stats(match: Match):
        """
        Updates wins/draws/losses for the head coaches involved in the match.
        """
        if match.home_score is None or match.away_score is None:
            return

        target_date = match.date.date() if match.date else None
        if not target_date:
            return

        def update_history(coach, club, result):
            if not coach or not club:
                return
            
            # Find the active history record for this coach at this club on the match date
            history = HistoricoTreinador.objects.filter(
                treinador=coach,
                clube=club,
                data_inicio__lte=target_date,
            ).filter(
                Q(data_fim__isnull=True) | Q(data_fim__gte=target_date)
            ).first()

            if history:
                history.jogos = F('jogos') + 1
                if result == 'win':
                    history.vitorias = F('vitorias') + 1
                elif result == 'draw':
                    history.empates = F('empates') + 1
                elif result == 'loss':
                    history.derrotas = F('derrotas') + 1
                history.save()

        # Determine results
        home_result = 'draw'
        away_result = 'draw'
        if match.home_score > match.away_score:
            home_result = 'win'
            away_result = 'loss'
        elif match.away_score > match.home_score:
            home_result = 'loss'
            away_result = 'win'

        update_history(match.home_coach, match.home_team, home_result)
        update_history(match.away_coach, match.away_team, away_result)

