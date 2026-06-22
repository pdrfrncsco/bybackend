from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import (
    OrganizacaoProfile,
    ClubeProfile,
    JogadorProfile,
    AdeptoProfile,
)

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'name', 'role')
        read_only_fields = fields


class OrganizacaoProfileSerializer(serializers.ModelSerializer):
    user_details = UserMiniSerializer(source='user', read_only=True)

    class Meta:
        model = OrganizacaoProfile
        fields = (
            'id',
            'user',
            'user_details',
            'nome',
            'sigla',
            'descricao',
            'email',
            'telefone',
            'website',
            'pais',
            'provincia',
            'cidade',
            'logo',
            'banner',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ClubeProfileSerializer(serializers.ModelSerializer):
    user_details = UserMiniSerializer(source='user', read_only=True)

    class Meta:
        model = ClubeProfile
        fields = (
            'id',
            'user',
            'user_details',
            'nome',
            'sigla',
            'fundacao',
            'historia',
            'email',
            'telefone',
            'website',
            'logo',
            'banner',
            'estadio',
            'cores',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class JogadorProfileSerializer(serializers.ModelSerializer):
    user_details = UserMiniSerializer(source='user', read_only=True)

    class Meta:
        model = JogadorProfile
        fields = (
            'id',
            'user',
            'user_details',
            'nome_completo',
            'nome_desportivo',
            'data_nascimento',
            'nacionalidade',
            'altura',
            'peso',
            'pe_preferencial',
            'posicao',
            'foto',
            'biografia',
            'agente',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class AdeptoProfileSerializer(serializers.ModelSerializer):
    user_details = UserMiniSerializer(source='user', read_only=True)
    clubes_favoritos_details = serializers.SerializerMethodField(read_only=True)
    jogadores_favoritos_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AdeptoProfile
        fields = (
            'id',
            'user',
            'user_details',
            'nome',
            'foto',
            'cidade',
            'pais',
            'clubes_favoritos',
            'clubes_favoritos_details',
            'jogadores_favoritos',
            'jogadores_favoritos_details',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_clubes_favoritos_details(self, obj):
        return [
            {
                'id': str(c.id),
                'nome': c.nome,
                'sigla': c.sigla,
                'logo': c.logo.url if c.logo else None
            }
            for c in obj.clubes_favoritos.all()
        ]

    def get_jogadores_favoritos_details(self, obj):
        return [
            {
                'id': str(j.id),
                'nome_completo': j.nome_completo,
                'nome_desportivo': j.nome_desportivo,
                'foto': j.foto.url if j.foto else None
            }
            for j in obj.jogadores_favoritos.all()
        ]
