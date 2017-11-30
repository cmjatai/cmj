import copy
import inspect

from django.core import serializers as django_serializers
from django.forms.models import model_to_dict
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.relations import RelatedField, ManyRelatedField,\
    MANY_RELATION_KWARGS

from cmj.sigad.models import Documento


class DocumentoParteField(RelatedField):
    queryset = Documento.objects.order_by('ordem')

    def to_representation(self, instance):
        cfg = self.configs
        if not cfg['depths'][cfg['field']]:
            return instance.pk

        inst = model_to_dict(instance, fields=cfg['fields'])

        inst[cfg['field']] = []

        if cfg['depths'][cfg['field']]:
            for child in getattr(instance, cfg['field']).order_by('ordem'):
                inst[cfg['field']].append(
                    cfg['serializer'](child, depths=cfg['depths']).data)

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


class DocumentoSerializer(serializers.ModelSerializer):

    childs = DocumentoParteField(many=True)
    documentos_citados = DocumentoParteField(many=True)

    def __init__(self, instance=None, data=empty, depths={}, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        meta = getattr(self, 'Meta', None)

        exclude = ()
        if meta:
            exclude = meta.exclude

        if depths:
            depths = {
                'childs': depths['childs'] - 1 if depths['childs'] else 0,
                'documentos_citados': depths[
                    'documentos_citados'] - 1
                if depths['documentos_citados'] else 0,
            }
        else:
            params = kwargs['context']['request'].query_params
            depths = {
                'childs': int(params.get('depth_childs', '0')),
                'documentos_citados': int(params.get('depth_citados', '0'))
            }

        for key, value in depths.items():

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

    class Meta:
        model = Documento
        exclude = ('old_json', 'old_path', )


class DocumentoUserAnonymousSerializer(DocumentoSerializer):
    childs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta(DocumentoSerializer.Meta):
        model = Documento
        exclude = ('old_json', 'old_path', 'owner')
