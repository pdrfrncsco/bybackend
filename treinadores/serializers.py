from rest_framework import serializers
from .models import Treinador, HistoricoTreinador, LicencaTreinador


class LicencaTreinadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicencaTreinador
        fields = [
            'id',
            'nome',
            'entidade',
            'data_emissao',
            'data_validade',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class HistoricoTreinadorSerializer(serializers.ModelSerializer):
    clube_nome = serializers.CharField(source='clube.name', read_only=True)

    class Meta:
        model = HistoricoTreinador
        fields = [
            'id',
            'treinador',
            'clube',
            'clube_nome',
            'cargo',
            'data_inicio',
            'data_fim',
            'jogos',
            'vitorias',
            'empates',
            'derrotas',
            'conquistas',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class HistoricoTreinadorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoTreinador
        fields = [
            'clube',
            'cargo',
            'data_inicio',
            'data_fim',
            'jogos',
            'vitorias',
            'empates',
            'derrotas',
            'conquistas',
        ]

    def validate(self, attrs):
        data_inicio = attrs.get('data_inicio')
        data_fim = attrs.get('data_fim')
        if data_fim is not None and data_inicio is not None and data_fim < data_inicio:
            raise serializers.ValidationError({'data_fim': 'data_fim não pode ser anterior à data_inicio.'})
        jogos = attrs.get('jogos', 0)
        vitorias = attrs.get('vitorias', 0)
        empates = attrs.get('empates', 0)
        derrotas = attrs.get('derrotas', 0)
        if vitorias + empates + derrotas > jogos:
            raise serializers.ValidationError({'jogos': 'jogos deve ser >= vitorias + empates + derrotas.'})
        return attrs


class EncerrarHistoricoTreinadorSerializer(serializers.Serializer):
    data_fim = serializers.DateField()


class TreinadorSerializer(serializers.ModelSerializer):
    historico = HistoricoTreinadorSerializer(many=True, read_only=True)
    licencas = LicencaTreinadorSerializer(many=True, read_only=True)

    class Meta:
        model = Treinador
        fields = [
            'id',
            'first_name',
            'last_name',
            'nacionalidade',
            'data_nascimento',
            'foto',
            'estilo_jogo',
            'biografia',
            'historico',
            'licencas',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

