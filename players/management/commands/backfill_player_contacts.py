from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from players.models import Player
try:
    from players.models.contact import PlayerContact
except Exception:
    # Fallback if contact exported differently
    try:
        from players.models import PlayerContact
    except Exception:
        PlayerContact = None

try:
    from media_assets.models import MediaAsset
except Exception:
    MediaAsset = None


class Command(BaseCommand):
    help = "Backfill PlayerContact from Player.email/phone and link profile_photo from existing MediaAsset by avatar URL"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')
        parser.add_argument('--limit', type=int, default=0, help='Limit number of players processed (0 = all)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        qs = Player.objects.all().order_by('id')
        total = qs.count()
        self.stdout.write(f'Found {total} players')
        if limit > 0:
            qs = qs[:limit]
            self.stdout.write(f'Limiting to first {limit} players')

        created_contacts = 0
        linked_photos = 0
        skipped = 0

        for player in qs:
            # Create PlayerContact if missing and we have contact data
            has_contact = False
            if PlayerContact is None:
                has_contact = True
            else:
                try:
                    has_contact = PlayerContact.objects.filter(player=player).exists()
                except Exception:
                    has_contact = True

            if not has_contact:
                email = getattr(player, 'email', None)
                phone = getattr(player, 'phone', None)
                if email or phone:
                    msg = f"Would create PlayerContact for player={player.id} (email={email}, phone={phone})"
                    if dry_run:
                        self.stdout.write('[DRY] ' + msg)
                    else:
                        with transaction.atomic():
                            try:
                                PlayerContact.objects.create(player=player, email=email or '', phone=phone or '')
                                created_contacts += 1
                                self.stdout.write('Created PlayerContact for player id=' + str(player.id))
                            except Exception as e:
                                self.stderr.write(f'Failed to create PlayerContact for player {player.id}: {e}')
                else:
                    skipped += 1
            # Link profile_photo if missing and avatar URL exists
            profile_photo = getattr(player, 'profile_photo', None)
            avatar = getattr(player, 'avatar', None)
            if (not profile_photo) and avatar and MediaAsset is not None:
                # try to find an existing MediaAsset with matching public_url
                asset = MediaAsset.objects.filter(public_url=avatar).first()
                if asset:
                    msg = f"Would link existing MediaAsset {asset.id} to player={player.id} as profile_photo"
                    if dry_run:
                        self.stdout.write('[DRY] ' + msg)
                    else:
                        try:
                            player.profile_photo = asset
                            player.save(update_fields=['profile_photo'])
                            linked_photos += 1
                            self.stdout.write(f'Linked MediaAsset {asset.id} to player id={player.id}')
                        except Exception as e:
                            self.stderr.write(f'Failed to link MediaAsset for player {player.id}: {e}')
                else:
                    # No matching asset found; skip
                    if dry_run:
                        self.stdout.write(f'[DRY] No MediaAsset found matching avatar URL for player id={player.id}')
                    else:
                        skipped += 1

        self.stdout.write('Backfill complete')
        self.stdout.write(f'PlayerContacts created: {created_contacts}')
        self.stdout.write(f'Profile photos linked: {linked_photos}')
        self.stdout.write(f'Players skipped (no contact data or no asset): {skipped}')
