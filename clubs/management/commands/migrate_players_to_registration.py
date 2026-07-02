"""
BOLAYETU — Migrate ClubMember Players to PlayerRegistration

This command migrates all ClubMember records with role="player" to
PlayerRegistration records, creating global Player entities as needed.

Architecture (06A_GLOBAL_AND_TENANT_DOMAIN.md):
    - Player is global, permanent
    - PlayerRegistration is tenant-scoped, temporary (per season/competition)
    - ClubMember should only be used for staff (non-players) after migration

Usage:
    python manage.py migrate_players_to_registration [--dry-run] [--club-id=UUID]

Options:
    --dry-run     Show what would be migrated without making changes
    --club-id     Only migrate players from a specific club
"""

import logging
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction

from clubs.models import Club, ClubMember
from clubs.constants import ClubMemberRole
from players.models import Player, PlayerRegistration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate ClubMember(role=player) to PlayerRegistration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without making changes",
        )
        parser.add_argument(
            "--club-id",
            type=str,
            help="Only migrate players from a specific club (UUID)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        club_id = options.get("club_id")

        # Get all player ClubMembers
        queryset = ClubMember.objects.filter(role=ClubMemberRole.PLAYER, is_active=True)
        
        if club_id:
            queryset = queryset.filter(club_id=club_id)
        
        total = queryset.count()
        
        self.stdout.write(f"Found {total} player ClubMembers to migrate")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for member in queryset.select_related("club", "user"):
            try:
                if dry_run:
                    self._dry_run_migrate(member)
                    migrated += 1
                else:
                    self._migrate_member(member)
                    migrated += 1
            except Exception as e:
                errors += 1
                self.stderr.write(self.style.ERROR(
                    f"Error migrating {member.display_name}: {e}"
                ))
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"DRY RUN complete: {migrated} would be migrated, {skipped} skipped, {errors} errors"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Migration complete: {migrated} migrated, {skipped} skipped, {errors} errors"
            ))

    def _dry_run_migrate(self, member: ClubMember) -> None:
        """Show what would happen for a single member."""
        player_name = member.display_name
        club_name = member.club.name
        
        # Check if Player already exists
        if member.user:
            existing_player = Player.objects.filter(user=member.user).first()
            if existing_player:
                self.stdout.write(f"  {player_name} -> existing Player {existing_player.slug}")
            else:
                self.stdout.write(f"  {player_name} -> NEW Player (linked to user)")
        else:
            self.stdout.write(f"  {player_name} -> NEW Player (no user link)")
        
        self.stdout.write(f"    Club: {club_name}")
        self.stdout.write(f"    Jersey: {member.jersey_number or 'N/A'}")
        self.stdout.write(f"    Position: {member.position or 'N/A'}")

    @transaction.atomic
    def _migrate_member(self, member: ClubMember) -> None:
        """Migrate a single ClubMember to PlayerRegistration."""
        from django.utils.text import slugify
        
        # Step 1: Find or create the global Player
        player = None
        
        if member.user:
            # Try to find existing player by user
            player = Player.objects.filter(user=member.user).first()
        
        if not player:
            # Create new Player
            name_parts = (member.full_name or member.display_name or "Unknown").split(maxsplit=1)
            first_name = name_parts[0] if name_parts else "Unknown"
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Generate unique slug
            base_slug = slugify(f"{first_name} {last_name}")
            slug = base_slug
            counter = 1
            while Player.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Map position from ClubMember to Player
            position_map = {
                "GK": "gk",
                "DF": "cb",
                "MF": "cm",
                "FW": "st",
            }
            primary_position = position_map.get(member.position, "multiple")
            
            player = Player.objects.create(
                first_name=first_name,
                last_name=last_name,
                slug=slug,
                primary_position=primary_position,
                user=member.user,
                status=Player.PlayerStatus.ACTIVE,
            )
            
            logger.info(f"Created Player: {player.slug}")
        
        # Step 2: Check for existing registration
        existing_reg = PlayerRegistration.objects.filter(
            player=player,
            club=member.club,
            status__in=["registered", "loaned"],
        ).first()
        
        if existing_reg:
            logger.info(f"Player {player.slug} already registered at {member.club.name}")
            return
        
        # Step 3: Create PlayerRegistration
        PlayerRegistration.objects.create(
            player=player,
            club=member.club,
            tenant=member.club.tenant,
            shirt_number=member.jersey_number,
            joined_date=member.joined_at or date.today(),
            status=PlayerRegistration.RegistrationStatus.REGISTERED,
        )
        
        logger.info(f"Created registration: {player.slug} @ {member.club.name}")
        
        # Step 4: Update ClubMember (mark as non-player to prevent duplicate migration)
        # We keep the record for historical purposes but change role
        member.role = "staff"  # Generic staff role for historical records
        member.is_active = False
        member.save(update_fields=["role", "is_active"])
