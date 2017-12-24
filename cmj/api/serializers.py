
from django.forms.models import model_to_dict
from django.utils import timezone
from model_utils.choices import Choices
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty, JSONField, ChoiceField,\
    SerializerMethodField, SlugField
from rest_framework.relations import RelatedField, ManyRelatedField,\
    MANY_RELATION_KWARGS

from cmj.sigad.models import Documento, ReferenciaEntreDocumentos,\
    DOC_TEMPLATES_CHOICE, CMSMixin


class DocumentoParteField(RelatedField):

    def to_representation(self, instance):
        cfg = self.configs

        if isinstance(instance, Documento):
            inst = model_to_dict(instance, fields=cfg['fields'])
            inst['has_midia'] = hasattr(instance, 'midia')
            inst[cfg['field']] = {}
        else:
            inst = model_to_dict(instance)
            inst['refresh'] = 0

        if not hasattr(instance, cfg['field']):
            return inst

        inst[cfg['field']] = {
            child.id: cfg['serializer'](child, m2ms=cfg['m2ms']).data
            for child in getattr(instance, cfg['field']).order_by('ordem')
        }

        return inst

    def to_internal_value(self, data):
        RelatedField.to_internal_value(self, data)

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

            def to_representation(self, iterable):
                return {
                    value.id: self.child_relation.to_representation(value)
                    for value in iterable
                }
        return CustomManyRelatedField(**list_kwargs)


class ReferenciaField(DocumentoParteField):
    queryset = ReferenciaEntreDocumentos.objects.all()

    def to_internal_value(self, data):
        return data


class DocumentoSerializer(serializers.ModelSerializer):

    # documentos_citados = DocumentoParteField(many=True)
    childs = DocumentoParteField(many=True, required=False, read_only=True)
    cita = ReferenciaField(many=True, required=False)

    has_midia = serializers.SerializerMethodField()
    refresh = serializers.SerializerMethodField()
    choices = SerializerMethodField()
    slug = SlugField(read_only=True)

    class Meta:
        model = Documento
        exclude = ('old_json',
                   'old_path',
                   'documentos_citados',
                   'owner',
                   'parlamentares',
                   'materias')

    def get_has_midia(self, obj):
        return hasattr(obj, 'midia')

    def get_refresh(self, obj):
        return 0

    def get_choices(self, obj):
        choices = {
            'tipo': {key: value.triple_map
                     for key, value in Documento.tipo_parte_doc.items()},
            'visibilidade': Documento.VISIBILIDADE_STATUS.triple_map,
            'alinhamento': Documento.alinhamento_choice.triple_map,
            'template_doc': DOC_TEMPLATES_CHOICE.triple_map,
        }

        choices['all_bycode'] = Documento.tipo_parte_doc_choice.triple_map
        choices['all_bycomponent'
                ] = Documento.tipo_parte_doc_choice.triple_map_component
        return choices

    def __init__(self, instance=None, data=empty, m2ms=[], **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        meta = getattr(self, 'Meta', None)

        exclude = ()
        if meta:
            exclude = meta.exclude

        if not m2ms:
            m2ms = ['childs', 'cita']

        for m2m in m2ms:

            if m2m not in self.fields.fields:
                continue

            child_relation = self.fields.fields.get(m2m).child_relation

            child_relation.configs = {
                'field': m2m,
                'serializer': DocumentoSerializer,
                'fields': [
                    field for field in self.fields.fields
                    if field not in meta.exclude

                ],
                'm2ms': m2ms
            }

    def update(self, instance, validated_data):
        vd = validated_data
        if 'visibilidade' in vd and \
                vd['visibilidade'] == Documento.STATUS_PUBLIC and\
                instance.visibilidade != Documento.STATUS_PUBLIC:
            vd['public_date'] = timezone.now()

        if 'ordem' in vd and vd['ordem']:
            ordem_atual = instance.ordem
            ordem_nova = vd['ordem']
            Documento.objects.remove_space(instance.parent, ordem_atual)
            Documento.objects.create_space(instance.parent, ordem_nova)

        if 'cita' in vd:
            cita = vd.pop('cita')
            if len(cita) == 1:
                cita = cita[0]
                ref = ReferenciaEntreDocumentos.objects.get(
                    pk=cita.pop('id'))

                if 'ordem' in cita:
                    ordem_atual = ref.ordem
                    ordem_nova = cita.pop('ordem')
                    ReferenciaEntreDocumentos.objects.remove_space(
                        instance, ordem_atual)
                    ReferenciaEntreDocumentos.objects.create_space(
                        instance, ordem_nova)
                    ref.ordem = ordem_nova

                for attr, value in cita.items():
                    setattr(instance, attr, value)
                ref.save()

            else:
                raise ValidationError(
                    _('Não existe implentação para tratar '
                      'mais de uma citação ao mesmo tempo.'))

        update = serializers.ModelSerializer.update(self, instance, vd)

        return update

    def create(self, validated_data):
        vd = validated_data
        vd['owner'] = self.context['request'].user

        if 'ordem' in vd and vd['ordem']:
            Documento.objects.create_space(vd['parent'], vd['ordem'])

        if 'classe' in vd and vd['classe']:
            vd['template_doc'] = vd['classe'].template_doc_padrao
            vd['tipo'] = vd['classe'].tipo_doc_padrao

            if vd['classe'].visibilidade != CMSMixin.STATUS_PUBLIC:
                vd['visibilidade'] = vd['classe'].visibilidade

        instance = serializers.ModelSerializer.create(self, validated_data)

        if not instance.is_parte_de_documento():
            container = Documento()
            container.titulo = ''
            container.descricao = ''
            container.classe = instance.classe
            container.tipo = Documento.TPD_CONTAINER_SIMPLES
            container.owner = instance.owner
            container.parent = instance
            container.ordem = 1
            container.visibilidade = instance.visibilidade
            container.save()
        else:
            if not instance.ordem:
                prev = instance.parent.childs.view_childs().last()
                if prev:
                    instance.ordem = prev.ordem + 1
                    instance.save()

        return instance


class DocumentoUserAnonymousSerializer(DocumentoSerializer):
    childs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta(DocumentoSerializer.Meta):
        model = Documento
        exclude = ('old_json', 'old_path', 'owner')
