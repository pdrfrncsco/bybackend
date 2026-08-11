"""
BOLAYETU — Player Agent Service Tests

Tests for PlayerAgentService methods.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta

from players.models import Player, Agent, PlayerAgentRelationship
from players.services.agent_service import (
    PlayerAgentService,
    AgentError,
    AgentRelationshipError,
)
from core.models import Tenant


class PlayerAgentServiceTestCase(TestCase):
    """Test PlayerAgentService methods."""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Test Org", slug="test-org")
        self.player = Player.objects.create(
            first_name="João",
            last_name="Silva",
            date_of_birth=date(1995, 5, 15),
            nationality="AO",
            primary_position="ST",
        )

    def test_create_agent(self):
        """Test creating a new agent."""
        agent = PlayerAgentService.create_agent(
            name="Carlos Mendes",
            country="PT",
            email="carlos@example.com",
            phone="+351912345678",
            agency_name="Mendes Sports Agency",
            agency_type=Agent.AgencyType.AGENCY,
            license_number="FIFA-12345",
        )

        self.assertEqual(agent.name, "Carlos Mendes")
        self.assertEqual(agent.country, "PT")
        self.assertEqual(agent.email, "carlos@example.com")
        self.assertTrue(agent.is_active)
        self.assertFalse(agent.verified)

    def test_create_agent_with_duplicate_fifa_id(self):
        """Test that duplicate FIFA agent IDs raise error."""
        PlayerAgentService.create_agent(
            name="Agent One",
            country="PT",
            email="agent1@example.com",
            phone="+351911111111",
            fifa_agent_id="FIFA-UNIQUE-001",
        )

        with self.assertRaises(AgentError):
            PlayerAgentService.create_agent(
                name="Agent Two",
                country="PT",
                email="agent2@example.com",
                phone="+351922222222",
                fifa_agent_id="FIFA-UNIQUE-001",
            )

    def test_verify_agent(self):
        """Test verifying an agent."""
        agent = PlayerAgentService.create_agent(
            name="To Verify",
            country="PT",
            email="verify@example.com",
            phone="+351913333333",
        )

        self.assertFalse(agent.verified)
        self.assertIsNone(agent.verified_at)

        verified_agent = PlayerAgentService.verify_agent(
            agent=agent,
            verified_by=None,  # In real test, would pass a User instance
        )

        self.assertTrue(verified_agent.verified)
        self.assertIsNotNone(verified_agent.verified_at)

    def test_create_relationship(self):
        """Test creating player-agent relationship."""
        agent = PlayerAgentService.create_agent(
            name="Relationship Agent",
            country="PT",
            email="rel@example.com",
            phone="+351914444444",
        )

        relationship = PlayerAgentService.create_relationship(
            player=self.player,
            agent=agent,
            start_date=date.today(),
            tenant=self.tenant,
            commission_rate=10.0,
        )

        self.assertEqual(relationship.player, self.player)
        self.assertEqual(relationship.agent, agent)
        self.assertEqual(relationship.status, PlayerAgentRelationship.RelationshipStatus.ACTIVE)
        self.assertEqual(relationship.commission_rate, 10.0)

    def test_create_relationship_duplicate_active(self):
        """Test that a player cannot have multiple active agents."""
        agent1 = PlayerAgentService.create_agent(
            name="Agent One",
            country="PT",
            email="agent1@example.com",
            phone="+351915555555",
            fifa_agent_id="FIFA-UNIQUE-001",  # Unique FIFA ID
        )
        agent2 = PlayerAgentService.create_agent(
            name="Agent Two",
            country="PT",
            email="agent2@example.com",
            phone="+351916666666",
            fifa_agent_id="FIFA-UNIQUE-002",  # Different unique FIFA ID
        )

        # Create first relationship
        PlayerAgentService.create_relationship(
            player=self.player,
            agent=agent1,
            start_date=date.today(),
        )

        # Try to create second active relationship
        with self.assertRaises(AgentRelationshipError):
            PlayerAgentService.create_relationship(
                player=self.player,
                agent=agent2,
                start_date=date.today(),
            )

    def test_terminate_relationship(self):
        """Test terminating a player-agent relationship."""
        agent = PlayerAgentService.create_agent(
            name="Terminate Agent",
            country="PT",
            email="term@example.com",
            phone="+351917777777",
        )

        relationship = PlayerAgentService.create_relationship(
            player=self.player,
            agent=agent,
            start_date=date.today(),
        )

        self.assertEqual(relationship.status, PlayerAgentRelationship.RelationshipStatus.ACTIVE)

        terminated = PlayerAgentService.terminate_relationship(
            relationship=relationship,
            reason="Mutual agreement",
        )

        self.assertEqual(terminated.status, PlayerAgentRelationship.RelationshipStatus.TERMINATED)

    def test_get_active_agent(self):
        """Test getting player's active agent."""
        agent = PlayerAgentService.create_agent(
            name="Active Agent",
            country="PT",
            email="active@example.com",
            phone="+351918888888",
        )

        PlayerAgentService.create_relationship(
            player=self.player,
            agent=agent,
            start_date=date.today(),
        )

        active = PlayerAgentService.get_active_agent(self.player)
        self.assertIsNotNone(active)
        self.assertEqual(active.agent, agent)

    def test_get_relationships_for_player(self):
        """Test getting all relationships for a player."""
        agent1 = PlayerAgentService.create_agent(
            name="Past Agent",
            country="PT",
            email="past@example.com",
            phone="+351919999999",
            fifa_agent_id="FIFA-UNIQUE-003",  # Unique FIFA ID
        )
        agent2 = PlayerAgentService.create_agent(
            name="Current Agent",
            country="PT",
            email="current@example.com",
            phone="+351910000000",
            fifa_agent_id="FIFA-UNIQUE-004",  # Different unique FIFA ID
        )

        # Create and terminate first relationship
        rel1 = PlayerAgentService.create_relationship(
            player=self.player,
            agent=agent1,
            start_date=date.today() - timedelta(days=365),
        )
        PlayerAgentService.terminate_relationship(rel1)

        # Create second relationship
        PlayerAgentService.create_relationship(
            player=self.player,
            agent=agent2,
            start_date=date.today(),
        )

        relationships = PlayerAgentService.get_relationships_for_player(self.player)
        self.assertEqual(len(relationships), 2)
