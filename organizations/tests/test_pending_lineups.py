import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Tenant
from clubs.models import Club
from competitions.models import Competition, Match, LineupSubmission
from accounts.models import TenantMembership
from accounts.constants import MembershipRole

User = get_user_model()


@pytest.mark.django_db
class TestOrganizationPendingLineups(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create tenant (organization)
        self.tenant = Tenant.objects.create(name='Org Pending Lineups')

        # Create user and membership (admin)
        self.user = User.objects.create_user(email='orgadmin@example.com', password='password')
        TenantMembership.objects.create(user=self.user, tenant=self.tenant, role=MembershipRole.OWNER, is_active=True)

        # Create competition, clubs and match
        self.competition = Competition.objects.create(tenant=self.tenant, name='Comp 1', season='2026')
        self.club = Club.objects.create(tenant=self.tenant, name='Club A', slug='club-a')
        self.other_club = Club.objects.create(tenant=self.tenant, name='Club B', slug='club-b')

        self.match = Match.objects.create(
            tenant=self.tenant,
            competition=self.competition,
            home_club=self.club,
            away_club=self.other_club,
            match_date=timezone.now(),
        )

        # Create a submitted lineup submission
        self.submission = LineupSubmission.objects.create(
            tenant=self.tenant,
            match=self.match,
            club=self.club,
            status=LineupSubmission.SubmissionStatus.SUBMITTED,
            submitted_at=timezone.now(),
        )

    def test_get_pending_lineups(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get('/api/v1/organizations/me/lineups/pending/')
        assert resp.status_code == 200
        data = resp.json()
        # Expect results in paginated response
        results = data.get('results') or data
        assert any(r.get('id') == str(self.submission.id) for r in results)
