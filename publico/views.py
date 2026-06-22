import logging

from django.conf import settings
from django.core.mail import send_mail
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AdvertiseContactSerializer, SupportContactSerializer


logger = logging.getLogger(__name__)


class AdvertiseContactView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = AdvertiseContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subject = "Novo pedido de publicidade"
        message = (
            f"Nome da empresa: {data['company_name']}\n"
            f"Pessoa de contacto: {data['contact_name']}\n"
            f"Email: {data['email']}\n"
            f"Telefone: {data['phone']}\n"
            f"Interesse principal: {data['interest']}\n\n"
            f"Mensagem:\n{data['message']}"
        )

        recipient = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if not recipient:
            return Response(
                {"detail": "Configuração de email não disponível."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Erro ao enviar email de pedido de publicidade")
            return Response(
                {"detail": "Erro ao enviar mensagem."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"detail": "Mensagem enviada com sucesso."},
            status=status.HTTP_201_CREATED,
        )


class SupportContactView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = SupportContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subject = "Novo pedido de suporte"
        message = (
            f"Nome: {data['full_name']}\n"
            f"Email: {data['email']}\n"
            f"Assunto: {data['subject']}\n\n"
            f"Mensagem:\n{data['message']}"
        )

        recipient = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if not recipient:
            return Response(
                {"detail": "Configuração de email não disponível."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Erro ao enviar email de suporte")
            return Response(
                {"detail": "Erro ao enviar mensagem."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"detail": "Mensagem enviada com sucesso."},
            status=status.HTTP_201_CREATED,
        )
