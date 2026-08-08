"""
BOLAYETU — Club Affiliation Request Model

Represents a formal request for a club to affiliate with an organization.
"""

from django.conf import settings
from django.db import models

from common.models import BaseModel


class ClubAffiliationRequest(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        PENDING = "pending", "Pendente"
        APPROVED = "approved", "Aprovado"
        REJECTED = "rejected", "Rejeitado"

    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="club_affiliation_requests",
        verbose_name="Organization",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="club_affiliation_requests_submitted",
        verbose_name="Submitted By",
    )
    name = models.CharField(max_length=255, verbose_name="Club Name")
    short_name = models.CharField(max_length=50, blank=True, default="", verbose_name="Short Name")
    founded_year = models.PositiveIntegerField(null=True, blank=True, verbose_name="Founded Year")
    city = models.CharField(max_length=255, null=True, blank=True, verbose_name="City")
    country = models.CharField(max_length=100, default="Angola", verbose_name="Country")
    email = models.EmailField(null=True, blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Phone")
    website = models.URLField(null=True, blank=True, verbose_name="Website")
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    primary_color = models.CharField(max_length=7, default="#014D40", verbose_name="Primary Color")
    secondary_color = models.CharField(max_length=7, default="#94D3C1", verbose_name="Secondary Color")
    stadium_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Stadium Name")
    stadium_capacity = models.PositiveIntegerField(null=True, blank=True, verbose_name="Stadium Capacity")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )
    review_notes = models.TextField(blank=True, default="", verbose_name="Review Notes")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="club_affiliation_requests_reviewed",
        verbose_name="Reviewed By",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Reviewed At")
    club = models.OneToOneField(
        "clubs.Club",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="affiliation_request",
        verbose_name="Created Club",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Club Affiliation Request"
        verbose_name_plural = "Club Affiliation Requests"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_club_affiliation_request_per_tenant_name",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} → {self.tenant.name}"


# Signal: Repair APPROVED requests created/edited directly in admin
def _repair_approved_affiliation_request(sender, instance: "ClubAffiliationRequest", created, **kwargs):
    """Ensure that an APPROVED request has a club and assign submitter as president.

    This covers cases where an admin marks a request APPROVED directly in Django admin
    and doesn't ensure the club/membership objects. It mirrors ClubAffiliationService.review_request
    behaviour for repair.
    """
    # Avoid import cycles
    if instance.status != ClubAffiliationRequest.Status.APPROVED:
        return

    try:
        from clubs.services.club_affiliation_service import ClubAffiliationService
        from clubs.services.club_service import ClubService
        from clubs.models import ClubMember
        from clubs.constants import ClubMemberRole, ClubStatus
    except Exception:
        return

    # If club exists and membership already set, nothing to do
    try:
        if instance.club_id is None:
            club = ClubAffiliationService._ensure_club_for_request(request_obj=instance)
            # Activate and assign membership
            if club.status != ClubStatus.ACTIVE:
                ClubService.activate(club=club)
            if instance.submitted_by_id:
                ClubMember.objects.update_or_create(
                    club=club,
                    user=instance.submitted_by,
                    defaults={
                        "role": ClubMemberRole.PRESIDENT,
                        "is_active": True,
                    },
                )
            instance.club = club
            instance.save(update_fields=["club", "updated_at"])  # type: ignore[arg-type]
    except Exception:
        # Swallow errors to avoid breaking admin save; errors are logged elsewhere.
        return


from django.db.models.signals import post_save
post_save.connect(_repair_approved_affiliation_request, sender=ClubAffiliationRequest)
