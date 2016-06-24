from rest_framework import serializers
from cmj.core.models import Trecho


class TrechoSearchSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    display = serializers.CharField()


class UfListingField(serializers.RelatedField):

    def to_representation(self, value):
        uf = value.uf
        return uf


class TrechoSerializer(serializers.Serializer):
    tipo_descricao = serializers.StringRelatedField(
        source='tipo')
    logradouro_descricao = serializers.StringRelatedField(
        source='logradouro')
    bairro_descricao = serializers.StringRelatedField(
        source='bairro')

    distrito_id = serializers.IntegerField()
    regiao_municipal_id = serializers.IntegerField()
    municipio_id = serializers.IntegerField()

    cep = serializers.StringRelatedField(many=True)
    uf = UfListingField(source='municipio', read_only=True)

    class Meta:
        model = Trecho
        fields = serializers.ALL_FIELDS
