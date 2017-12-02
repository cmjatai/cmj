
from django.forms.models import model_to_dict
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.relations import RelatedField, ManyRelatedField,\
    MANY_RELATION_KWARGS

from cmj.sigad.models import Documento, ReferenciaEntreDocumentos


class DocumentoParteField(RelatedField):
    queryset = Documento.objects.order_by('ordem')

    def to_representation(self, instance):
        cfg = self.configs

        """if not cfg['depths'][cfg['field']]:
            return instance.pk

        depths = copy.deepcopy(cfg['depths'])
        depth = depths[cfg['field']]
        depths[cfg['field']] = (depth - 1) if depth else 0"""

        if isinstance(instance, Documento):
            inst = model_to_dict(instance, fields=cfg['fields'])
        else:
            inst = model_to_dict(instance)

        inst[cfg['field']] = []

        # if depths[cfg['field']]:

        if not hasattr(instance, cfg['field']):
            return inst

        for child in getattr(instance, cfg['field']).order_by('ordem'):
            inst[cfg['field']].append(
                cfg['serializer'](child, depths=cfg['depths']).data)  # depths

        return inst

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_kwargs = {'child_relation': cls(*args, **kwargs)}
        for key in kwargs.keys():
            if key in MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]

        class CustomManyRelatedField(ManyRelatedField):

            def get_attribute(self, instance):
                relationship = super().get_attribute(instance)
                return relationship.order_by('ordem')

        return CustomManyRelatedField(**list_kwargs)


class RefereniciaDocumentoField(DocumentoParteField):
    queryset = ReferenciaEntreDocumentos.objects.order_by('ordem')


class DocumentoSerializer(serializers.ModelSerializer):

    childs = DocumentoParteField(many=True, required=False)
    # documentos_citados = DocumentoParteField(many=True)
    # cita = RefereniciaDocumentoField(many=True)

    class Meta:
        model = Documento
        exclude = ('old_json',
                   'old_path',
                   'documentos_citados',
                   'slug',
                   'owner',
                   'parlamentares',
                   'materias')

    def __init__(self, instance=None, data=empty, depths={}, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        meta = getattr(self, 'Meta', None)

        exclude = ()
        if meta:
            exclude = meta.exclude

        if not depths:
            params = kwargs['context']['request'].query_params
            depths = {
                'childs': int(params.get('depth_childs', '0')),
                # 'documentos_citados': int(params.get('depth_citados', '0')),
                # 'cita': int(params.get('depth_citados', '0'))
            }

        for key, value in depths.items():

            if key not in self.fields.fields:
                continue

            child_relation = self.fields.fields.get(key).child_relation

            child_relation.configs = {
                'field': key,
                'serializer': DocumentoSerializer,
                'fields': [
                    field for field in self.fields.fields
                    if field not in meta.exclude

                ],
                'depths': depths
            }

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return serializers.ModelSerializer.create(self, validated_data)


class DocumentoUserAnonymousSerializer(DocumentoSerializer):
    childs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta(DocumentoSerializer.Meta):
        model = Documento
        exclude = ('old_json', 'old_path', 'owner')
