import logging

from django.db import transaction
from django.utils.text import slugify

from core.models import Tenant
from competitions.constants import CompetitionStatus
from competitions.exceptions import CompetitionNotFound, DuplicateCompetition
from competitions.models import Competition
from competitions.selectors import CompetitionSelector

logger = logging.getLogger(__name__)


class CompetitionService:
    @staticmethod
    @transaction.atomic
    def create_competition(
        *,
        tenant: Tenant,
        name: str,
        competition_type: str,
        season: str,
        status: str = CompetitionStatus.DRAFT,
    ) -> Competition:
        slug = slugify(name) or "competition"
        if Competition.objects.filter(
            tenant=tenant,
            slug=slug,
            season=season,
        ).exists():
            raise DuplicateCompetition()

        competition = Competition.objects.create(
            tenant=tenant,
            name=name,
            slug=slug,
            competition_type=competition_type,
            season=season,
            status=status,
        )
        logger.info("Competition created: %s (%s)", competition.name, competition.id)
        return competition

    @staticmethod
    @transaction.atomic
    def update_competition(*, competition: Competition, **kwargs) -> Competition:
        updatable_fields = ["name", "competition_type", "season", "status"]
        updated_fields = ["updated_at"]

        for field in updatable_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(competition, field, kwargs[field])
                updated_fields.append(field)

        if "name" in kwargs and kwargs["name"] is not None:
            competition.slug = slugify(kwargs["name"]) or competition.slug
            updated_fields.append("slug")

        competition.save(update_fields=list(dict.fromkeys(updated_fields)))
        logger.info("Competition updated: %s (%s)", competition.name, competition.id)
        return competition

    @staticmethod
    def get_competition_for_tenant(*, tenant: Tenant, competition_id) -> Competition:
        competition = CompetitionSelector.get_by_id(
            tenant=tenant,
            competition_id=competition_id,
        )
        if competition is None:
            raise CompetitionNotFound()
        return competition
