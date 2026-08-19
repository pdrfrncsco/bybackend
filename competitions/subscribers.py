"""Domain subscribers for MatchCenter side effects."""

import logging

from core.events import Event, EventType, subscribe
from competitions.models import Competition, Match
from competitions.services.standing_service import StandingService

logger = logging.getLogger("competitions")


@subscribe(EventType.MATCH_FINISHED)
def handle_match_finished(event: Event) -> None:
    """Rebuild standings and knockout progression after the official result."""
    payload = event.payload or {}
    try:
        match = Match.objects.select_related("competition", "tenant").get(
            id=payload["match_id"], tenant_id=event.tenant_id,
        )
        StandingService.recalculate_standings(tenant=match.tenant, competition=match.competition)
        if match.competition.competition_type in {"cup", "tournament"}:
            from competitions.services.competition_format_service import CompetitionFormatService
            CompetitionFormatService.advance_knockout_rounds(
                tenant=match.tenant, competition=match.competition,
            )
    except (KeyError, Match.DoesNotExist):
        logger.warning("Unable to process MatchFinished event %s", event.id)
    except Exception:
        logger.exception("MatchFinished subscriber failed for event %s", event.id)


@subscribe(EventType.MATCH_ARCHIVED)
def handle_match_archived(event: Event) -> None:
    """Keep archival as an observable domain action for history integrations."""
    logger.info("Match archived: %s", (event.payload or {}).get("match_id"))
