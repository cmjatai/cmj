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

        inst = model_to_dict(instance, fields=self.fields)

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

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        meta = getattr(self, 'Meta', None)

        exclude = ()
        if meta:
            exclude = meta.exclude
        self.fields.fields.get('childs').child_relation.fields = [
            field for field in self.fields.fields
            if field not in meta.exclude]

    class Meta:
        model = Documento
        exclude = ('old_json', 'old_path', )


class DocumentoUserAnonymousSerializer(DocumentoSerializer):
    childs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta(DocumentoSerializer.Meta):
        model = Documento
        exclude = ('old_json', 'old_path', 'owner')
