from django.conf import settings
from django.db.models import Q
from django.urls.base import reverse
from django.utils import timezone
from rest_framework import serializers
from rest_framework.relations import StringRelatedField

from sapl.base.models import Autor, CasaLegislativa
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import SessaoPlenaria


class IntRelatedField(StringRelatedField):
    def to_representation(self, value):
        return int(value)


class ChoiceSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    def get_text(self, obj):
        return obj[1]

    def get_value(self, obj):
        return obj[0]


class ModelChoiceSerializer(ChoiceSerializer):

    def get_text(self, obj):
        return str(obj)

    def get_value(self, obj):
        return obj.id


class ModelChoiceObjectRelatedField(serializers.RelatedField):

    def to_representation(self, value):
        return ModelChoiceSerializer(value).data


class AutorSerializer(serializers.ModelSerializer):
    # AutorSerializer sendo utilizado pelo gerador automático da api devidos aos
    # critérios anotados em views.py

    autor_related = ModelChoiceObjectRelatedField(read_only=True)

    class Meta:
        model = Autor
        fields = '__all__'


class CasaLegislativaSerializer(serializers.ModelSerializer):
    version = serializers.SerializerMethodField()

    def get_version(self, obj):
        return settings.PORTALCMJ_VERSION

    class Meta:
        model = CasaLegislativa
        fields = '__all__'


class SessaoPlenariaSerializer(serializers.ModelSerializer):

    class Meta:
        model = SessaoPlenaria
        """fields = list(
            map(
                lambda x: x.name,
                SessaoPlenaria._meta.get_fields()
            )
        ) + ['legislatura']"""


class ParlamentarSerializer(serializers.ModelSerializer):

    class Meta:
        model = Parlamentar
        exclude = ["cpf", "rg", "fax",
                   "endereco_residencia", "municipio_residencia",
                   "uf_residencia", "cep_residencia", "situacao_militar",
                   "telefone_residencia", "titulo_eleitor", "fax_residencia"]


class ParlamentarEditSerializer(serializers.ModelSerializer):

    class Meta:
        model = Parlamentar
        fields = '__all__'


class MateriaLegislativaSerializer(serializers.ModelSerializer):
    anexadas = serializers.SerializerMethodField()
    desanexadas = serializers.SerializerMethodField()

    class Meta:
        model = MateriaLegislativa
        fields = '__all__'

    def get_anexadas(self, obj):
        return obj.anexadas.materias_anexadas().values_list('id', flat=True)

    def get_desanexadas(self, obj):
        return obj.anexadas.materias_desanexadas().values_list('id', flat=True)
