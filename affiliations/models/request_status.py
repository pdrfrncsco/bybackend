from django.db import models


class RequestStatus(models.TextChoices):
    PENDING = "PENDING", "Pendente"
    APPROVED = "APPROVED", "Aprovado"
    REJECTED = "REJECTED", "Rejeitado"
