from rest_framework import serializers
from affiliations.models import ClubeOrganizacaoRequest, JogadorClubeRequest, JogadorHistoricoClube


class ClubeProfileMiniSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    nome = serializers.CharField(read_only=True)
    sigla = serializers.CharField(read_only=True)
    logo = serializers.ImageField(read_only=True)


class OrganizacaoProfileMiniSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    nome = serializers.CharField(read_only=True)
    sigla = serializers.CharField(read_only=True)
    logo = serializers.ImageField(read_only=True)


class JogadorProfileMiniSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    nome_completo = serializers.CharField(read_only=True)
    nome_desportivo = serializers.CharField(read_only=True)
    foto = serializers.ImageField(read_only=True)


class ClubeOrganizacaoRequestSerializer(serializers.ModelSerializer):
    clube_details = ClubeProfileMiniSerializer(source='clube', read_only=True)
    organizacao_details = OrganizacaoProfileMiniSerializer(source='organizacao', read_only=True)

    class Meta:
        model = ClubeOrganizacaoRequest
        fields = (
            'id',
            'clube',
            'clube_details',
            'organizacao',
            'organizacao_details',
            'estado',
            'mensagem',
            'data_pedido',
            'data_decisao',
        )
        read_only_fields = ('id', 'estado', 'data_pedido', 'data_decisao')


class JogadorClubeRequestSerializer(serializers.ModelSerializer):
    jogador_details = JogadorProfileMiniSerializer(source='jogador', read_only=True)
    clube_details = ClubeProfileMiniSerializer(source='clube', read_only=True)

    class Meta:
        model = JogadorClubeRequest
        fields = (
            'id',
            'jogador',
            'jogador_details',
            'clube',
            'clube_details',
            'estado',
            'mensagem',
            'data_pedido',
            'data_decisao',
        )
        read_only_fields = ('id', 'estado', 'data_pedido', 'data_decisao')


class JogadorHistoricoClubeSerializer(serializers.ModelSerializer):
    jogador_details = JogadorProfileMiniSerializer(source='jogador', read_only=True)
    clube_details = ClubeProfileMiniSerializer(source='clube', read_only=True)

    class Meta:
        model = JogadorHistoricoClube
        fields = (
            'id',
            'jogador',
            'jogador_details',
            'clube',
            'clube_details',
            'data_inicio',
            'data_fim',
            'numero_camisola',
            'observacoes',
        )
        read_only_fields = ('id',)
