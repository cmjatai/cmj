from django.conf import settings
from django.urls.base import reverse
from rest_framework import serializers
from rest_framework.relations import StringRelatedField

from sapl.base.models import Autor, CasaLegislativa
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
        exclude = ["fax", "endereco_residencia", "municipio_residencia",
                   "uf_residencia", "cep_residencia", "telefone_residencia",
                   "titulo_eleitor", "fax_residencia"]
