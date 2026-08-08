import logging
from django.db import transaction

from players.models import PlayerContact

logger = logging.getLogger(__name__)


class PlayerContactService:
    @staticmethod
    @transaction.atomic
    def upsert_contact(*, player, data) -> PlayerContact:
        contact, created = PlayerContact.objects.get_or_create(player=player)
        for k, v in data.items():
            setattr(contact, k, v)
        contact.save()
        return contact

    @staticmethod
    @transaction.atomic
    def remove_contact(*, contact: PlayerContact) -> None:
        contact.delete()
