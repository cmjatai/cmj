import os
from decimal import Decimal

from django.db.models import Max
from django.forms.models import model_to_dict
from django.urls.base import reverse
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.fields import SerializerMethodField, SlugField, empty
from rest_framework.relations import (
    MANY_RELATION_KWARGS,
    ManyRelatedField,
    RelatedField,
)

from cmj.arq.models import ArqClasse, ArqDoc, DraftMidia
from cmj.core.models import Bi
from cmj.loa.models import EmendaLoa, PrestacaoContaRegistro, RegistroAjusteLoa
from cmj.sigad.models import (
    DOC_TEMPLATES_CHOICE,
    CMSMixin,
    Documento,
    ReferenciaEntreDocumentos,
)
from drfautoapi.drfautoapi import DrfAutoApiSerializerMixin


class CmjSerializerMixin(DrfAutoApiSerializerMixin):
    link_detail_backend = serializers.SerializerMethodField()

    class Meta(DrfAutoApiSerializerMixin.Meta):
        fields = "__all__"

    def get_link_detail_backend(self, obj) -> str:
        try:
            return reverse(
                f"{self.Meta.model._meta.app_config.name}:{self.Meta.model._meta.model_name}_detail",
                kwargs={"pk": obj.pk},
            )
        except:
            return ""


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


@extend_schema_field({"type": "string"})
class ModelChoiceObjectRelatedField(serializers.RelatedField):

    def to_representation(self, value):
        return ModelChoiceSerializer(value).data


class DocumentoChoiceSerializer(ModelChoiceSerializer):

    def get_text(self, obj):
        return obj.titulo

    class Meta:
        model = Documento
        fields = ["id", "titulo"]


class DocumentoParteField(RelatedField):

    def to_representation(self, instance):
        cfg = self.configs

        if isinstance(instance, Documento):
            inst = cfg["serializer"](instance).data
            # inst = model_to_dict(instance, fields=cfg['fields'])

            inst["has_midia"] = hasattr(instance, "midia")
            inst[cfg["field"]] = {}
        else:
            inst = model_to_dict(instance)
            inst["refresh"] = 0

        if not hasattr(instance, cfg["field"]):
            return inst

        inst[cfg["field"]] = {
            child.id: cfg["serializer"](child, m2ms=cfg["m2ms"]).data
            for child in getattr(instance, cfg["field"]).order_by("ordem")
        }
        return inst

    def to_internal_value(self, data):
        RelatedField.to_internal_value(self, data)

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_kwargs = {"child_relation": cls(*args, **kwargs)}
        for key in kwargs.keys():
            if key in MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]

        class CustomManyRelatedField(ManyRelatedField):

            def get_attribute(self, instance):
                relationship = super().get_attribute(instance)
                return relationship.order_by("ordem")

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


class BiSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bi
        fields = "__all__"


class DocumentoSerializer(serializers.ModelSerializer):

    # documentos_citados = DocumentoParteField(many=True)
    childs = DocumentoParteField(many=True, required=False, read_only=True)
    cita = ReferenciaField(many=True, required=False)

    has_midia = serializers.SerializerMethodField()
    mime_type = serializers.SerializerMethodField()
    refresh = serializers.SerializerMethodField()
    choices = SerializerMethodField()
    slug = SlugField(read_only=True)

    class Meta:
        model = Documento
        exclude = (
            "old_json",
            "old_path",
            "documentos_citados",
            "owner",
            "parlamentares",
            "materias",
        )

    def get_has_midia(self, obj):
        return hasattr(obj, "midia")

    def get_mime_type(self, obj):
        return obj.midia.last.content_type if hasattr(obj, "midia") else ""

    def get_refresh(self, obj):
        return 0

    def get_choices(self, obj):
        if obj.tipo not in CMSMixin.TDs:
            return {}
        choices = {
            "tipo": {
                key: value.triple_map for key, value in Documento.tipo_parte_doc.items()
            },
            "visibilidade": Documento.VISIBILIDADE_STATUS.triple_map,
            "alinhamento": Documento.alinhamento_choice.triple_map,
            "template_doc": DOC_TEMPLATES_CHOICE.triple_map,
        }

        choices["all_bycode"] = Documento.tipo_parte_doc_choice.triple_map
        choices["all_bycomponent"] = (
            Documento.tipo_parte_doc_choice.triple_map_component
        )
        return choices

    def __init__(self, instance=None, data=empty, m2ms=[], **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        meta = getattr(self, "Meta", None)

        exclude = ()
        if meta:
            exclude = meta.exclude

        if not m2ms:
            m2ms = ["childs", "cita"]

        for m2m in m2ms:

            if m2m not in self.fields.fields:
                continue

            child_relation = self.fields.fields.get(m2m).child_relation

            child_relation.configs = {
                "field": m2m,
                "serializer": DocumentoSerializer,
                "fields": [
                    field for field in self.fields.fields if field not in meta.exclude
                ],
                "m2ms": m2ms,
            }

    def update(self, instance, validated_data):
        vd = validated_data
        if (
            "visibilidade" in vd
            and vd["visibilidade"] == Documento.STATUS_PUBLIC
            and instance.visibilidade != Documento.STATUS_PUBLIC
        ):
            vd["public_date"] = timezone.now()

        if "ordem" in vd and vd["ordem"]:
            ordem_atual = instance.ordem
            ordem_nova = vd["ordem"]
            Documento.objects.remove_space(instance.parent, ordem_atual)
            Documento.objects.create_space(instance.parent, ordem_nova)

        if "cita" in vd:
            cita = vd.pop("cita")
            if len(cita) == 1:
                cita = cita[0]
                if "id" not in cita:
                    ordem = cita["ordem"]
                    if cita["ordem"] == 0:
                        max_ordem = ReferenciaEntreDocumentos.objects.filter(
                            referente=instance
                        ).aggregate(Max("ordem"))
                        ordem = (
                            (max_ordem["ordem__max"] + 1)
                            if max_ordem["ordem__max"]
                            else 1
                        )
                    else:
                        ReferenciaEntreDocumentos.objects.create_space(
                            instance, cita["ordem"]
                        )
                    ref = ReferenciaEntreDocumentos()
                    ref.ordem = ordem
                    ref.referenciado_id = cita["referenciado"]
                    ref.referente_id = cita["referente"]
                    ref.save()

                else:
                    ref = ReferenciaEntreDocumentos.objects.get(pk=cita.pop("id"))

                    if "ordem" in cita:
                        ordem_atual = ref.ordem
                        ordem_nova = cita.pop("ordem")
                        ReferenciaEntreDocumentos.objects.remove_space(
                            instance, ordem_atual
                        )
                        ReferenciaEntreDocumentos.objects.create_space(
                            instance, ordem_nova
                        )
                        ref.ordem = ordem_nova

                    for attr, value in cita.items():
                        setattr(ref, attr, value)
                    ref.save()

            else:
                raise DRFValidationError(
                    _(
                        "Não existe implentação para tratar "
                        "mais de uma citação ao mesmo tempo."
                    )
                )
        else:
            instance = serializers.ModelSerializer.update(self, instance, vd)

        return instance

    def create(self, validated_data):
        vd = validated_data
        vd["owner"] = self.context["request"].user

        if "ordem" in vd and vd["ordem"]:
            Documento.objects.create_space(vd["parent"], vd["ordem"])

        if "classe" in vd and vd["classe"]:
            vd["template_doc"] = vd["classe"].template_doc_padrao
            vd["tipo"] = vd["classe"].tipo_doc_padrao

            if vd["classe"].visibilidade != CMSMixin.STATUS_PUBLIC:
                vd["visibilidade"] = vd["classe"].visibilidade

        instance = serializers.ModelSerializer.create(self, validated_data)

        if not instance.is_parte_de_documento():
            container = Documento()
            container.titulo = ""
            container.descricao = ""
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
        exclude = ("old_json", "old_path", "owner")


class DraftMidiaSerializer(CmjSerializerMixin):
    arquivo_size = serializers.SerializerMethodField()

    def get_arquivo_size(self, obj):
        try:
            if not obj.arquivo:
                return 0

            size = os.path.getsize(obj.arquivo.path)
            return size, round(size / 1024 / 1024, 1)
        except Exception as e:
            return 0

    class Meta(CmjSerializerMixin.Meta):
        model = DraftMidia


class ArqClasseSerializer(CmjSerializerMixin):

    parents = serializers.SerializerMethodField()
    conta = serializers.SerializerMethodField()

    count_childs = serializers.SerializerMethodField()

    def get_parents(self, obj):
        return map(lambda x: {"id": x.id, "titulo": x.titulo}, obj.parents)

    def get_conta(self, obj):
        return obj.conta

    def get_count_childs(self, obj):
        return obj.childs.count()

    class Meta(CmjSerializerMixin.Meta):
        model = ArqClasse


class ArqDocSerializer(CmjSerializerMixin):

    def get_link_detail_backend(self, obj) -> str:
        try:
            return reverse(
                f"{self.Meta.model._meta.app_config.name}:{self.Meta.model._meta.model_name}_detail",
                kwargs={"classe_id": obj.classe_estrutural_id, "pk": obj.pk},
            )
        except:
            return ""

    class Meta(CmjSerializerMixin.Meta):
        model = ArqDoc


class RegistroAjusteLoaSerializer(CmjSerializerMixin):
    str_valor = serializers.CharField(read_only=True)

    # crie o campo valor como DecimalField chamanado método para calcular
    valor = serializers.SerializerMethodField()

    fase_prestacao_contas = serializers.SerializerMethodField()
    class Meta(CmjSerializerMixin.Meta):
        model = RegistroAjusteLoa

    def get_fase_prestacao_contas(self, obj):
        if obj.prestacaocontaregistro_set.filter(situacao=PrestacaoContaRegistro.SituacaoChoices.FINALIZADO).exists():
            return PrestacaoContaRegistro.SituacaoChoices.FINALIZADO
        elif obj.prestacaocontaregistro_set.filter(situacao=PrestacaoContaRegistro.SituacaoChoices.EM_EXECUCAO).exists():
            return PrestacaoContaRegistro.SituacaoChoices.EM_EXECUCAO
        else:
            return 'SEM_PRESTACAO_CONTAS'


    def get_valor(self, obj):
        obj = obj.registroajusteloaparlamentar_set.aggregate(total=Max("valor"))
        return obj["total"] if obj["total"] else 0


class EmendaLoaSerializer(CmjSerializerMixin):

    str_valor = serializers.CharField(
        read_only=True,
    )

    str_valor_computado = serializers.CharField(
        read_only=True,
    )

    finalidade_format = serializers.CharField(
        read_only=True,
    )

    ementa_format = serializers.CharField(
        read_only=True,
    )

    epigrafe_short = serializers.SerializerMethodField()

    valor_inicial = serializers.SerializerMethodField()
    valor_computado = serializers.FloatField(read_only=True)

    class Meta(CmjSerializerMixin.Meta):
        model = EmendaLoa

    def get_epigrafe_short(self, obj):
        if obj.materia and obj.materia.epigrafe_short:
            return obj.materia.epigrafe_short
        return ""

    def get_valor_inicial(self, obj):
        return obj.valor or Decimal("0.00")

    def validate_valor(self, obj, *args, **kwargs):

        obj = obj or "0.00"

        try:
            if obj and "." in obj and "," in obj:
                if obj.rindex(",") > obj.rindex("."):
                    obj = obj.replace(".", "").replace(",", ".")
                else:
                    obj = obj.replace(",", "")
            elif obj and "," in obj:
                obj = obj.replace(",", ".")

            obj = Decimal(obj)
        except:
            raise DRFValidationError(
                _(
                    'O campo "Valor Global da Emenda" deve ser prenchido e '
                    "seguir o formado 999.999.999,99. "
                )
            )

        if obj == Decimal("0.00"):
            raise DRFValidationError(
                _(
                    'O campo "Valor Global da Emenda" deve ser prenchido e '
                    "seguir o formado 999.999.999,99. "
                )
            )

        return obj
