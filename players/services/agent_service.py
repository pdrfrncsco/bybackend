"""
PlayerAgentService

Handles creation, termination, and management of player-agent relationships.
"""

import logging
from datetime import date
from typing import Optional

from django.db import transaction

from players.models import Player, Agent, PlayerAgentRelationship

logger = logging.getLogger("players")


class PlayerAgentService:
    """Service for managing player-agent relationships."""

    @staticmethod
    @transaction.atomic
    def create_agent(
        name: str,
        country: str,
        email: str,
        phone: str,
        agency_name: str = "",
        agency_type: str = Agent.AgencyType.INDIVIDUAL,
        license_number: str = "",
        fifa_agent_id: str = "",
        website: str = "",
        address: str = "",
        city: str = "",
        postal_code: str = "",
    ) -> Agent:
        """Create a new sports agent.

        Raises AgentError if creation fails.
        """
        # Check for duplicate FIFA agent ID if provided
        if fifa_agent_id and Agent.objects.filter(fifa_agent_id=fifa_agent_id).exists():
            raise AgentError(
                f"Agent with FIFA ID {fifa_agent_id} already exists."
            )

        agent = Agent.objects.create(
            name=name.strip(),
            agency_name=agency_name.strip(),
            agency_type=agency_type,
            license_number=license_number,
            fifa_agent_id=fifa_agent_id,
            country=country,
            email=email,
            phone=phone,
            website=website,
            address=address,
            city=city,
            postal_code=postal_code,
        )

        logger.info("Agent created: %s (%s)", agent.name, agent.id)
        return agent

    @staticmethod
    @transaction.atomic
    def verify_agent(agent: Agent, verified_by) -> Agent:
        """Verify an agent's credentials.

        Only platform admins or org admins should call this.
        """
        from django.utils import timezone

        agent.verified = True
        agent.verified_at = timezone.now()
        agent.save(update_fields=["verified", "verified_at"])

        logger.info("Agent verified: %s by %s", agent.name, verified_by)
        return agent

    @staticmethod
    @transaction.atomic
    def create_relationship(
        player: Player,
        agent: Agent,
        start_date: date,
        tenant=None,
        end_date: Optional[date] = None,
        commission_rate: Optional[float] = None,
        representation_agreement=None,
        notes: str = "",
    ) -> PlayerAgentRelationship:
        """Create a player-agent representation agreement.

        Raises AgentRelationshipError if an active relationship already exists.
        """
        # Check for existing active relationship
        active = PlayerAgentRelationship.objects.filter(
            player=player,
            status=PlayerAgentRelationship.RelationshipStatus.ACTIVE,
        ).first()

        if active:
            raise AgentRelationshipError(
                f"Player {player.full_name} already has an active agent: {active.agent.name}."
            )

        relationship = PlayerAgentRelationship.objects.create(
            player=player,
            agent=agent,
            tenant=tenant,
            start_date=start_date,
            end_date=end_date,
            status=PlayerAgentRelationship.RelationshipStatus.ACTIVE,
            commission_rate=commission_rate,
            representation_agreement=representation_agreement,
            notes=notes,
        )

        logger.info(
            "Agent relationship created: %s → %s",
            player.full_name,
            agent.name,
        )
        return relationship

    @staticmethod
    @transaction.atomic
    def terminate_relationship(
        relationship: PlayerAgentRelationship,
        reason: Optional[str] = None,
    ) -> PlayerAgentRelationship:
        """Terminate a player-agent relationship."""
        relationship.status = PlayerAgentRelationship.RelationshipStatus.TERMINATED
        relationship.save(update_fields=["status"])

        logger.info(
            "Agent relationship terminated: %s ← %s (reason: %s)",
            relationship.player.full_name,
            relationship.agent.name,
            reason or "not specified",
        )
        return relationship

    @staticmethod
    @transaction.atomic
    def suspend_relationship(
        relationship: PlayerAgentRelationship,
        reason: Optional[str] = None,
    ) -> PlayerAgentRelationship:
        """Suspend a player-agent relationship temporarily."""
        relationship.status = PlayerAgentRelationship.RelationshipStatus.SUSPENDED
        relationship.save(update_fields=["status"])

        logger.info(
            "Agent relationship suspended: %s ← %s (reason: %s)",
            relationship.player.full_name,
            relationship.agent.name,
            reason or "not specified",
        )
        return relationship

    @staticmethod
    def get_active_agent(player: Player) -> Optional[PlayerAgentRelationship]:
        """Get the currently active agent relationship for a player."""
        return PlayerAgentRelationship.objects.filter(
            player=player,
            status=PlayerAgentRelationship.RelationshipStatus.ACTIVE,
        ).select_related("agent").first()

    @staticmethod
    def get_relationships_for_player(player: Player):
        """Get all agent relationships for a player, ordered by most recent."""
        return PlayerAgentRelationship.objects.filter(
            player=player
        ).select_related("agent").order_by("-start_date")

    @staticmethod
    def get_players_for_agent(agent: Agent):
        """Get all player relationships for an agent, ordered by most recent."""
        return PlayerAgentRelationship.objects.filter(
            agent=agent,
            status=PlayerAgentRelationship.RelationshipStatus.ACTIVE,
        ).select_related("player").order_by("-start_date")


class AgentError(Exception):
    """Raised when an agent operation fails."""
    pass


class AgentRelationshipError(Exception):
    """Raised when a player-agent relationship operation fails."""
    pass
