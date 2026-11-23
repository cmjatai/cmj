import os

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Max
from django.forms.models import model_to_dict
from django.urls.base import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
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
from cmj.sigad.models import (
    DOC_TEMPLATES_CHOICE,
    CMSMixin,
    Documento,
    ReferenciaEntreDocumentos,
)
from drfautoapi.drfautoapi import DrfAutoApiSerializerMixin


class CmjSerializerMixin(DrfAutoApiSerializerMixin):
    """Serializer padrão das rotas geradas (docs/specs/api/serializacao.md).

    Leitura, em qualquer caminho que use o serializer:

    - os campos ``ip`` e ``user`` de um model que guarda quem fez o
      registro, isto é, que tem o par, só saem para superusuário;
    - dentro de ``metadata``, as chaves que descrevem onde os arquivos do
      registro estão armazenados só saem para superusuário;
    - as demais relações com o model de usuário só saem para quem tem a
      permissão de listagem do próprio model.

    Gravação:

    - ``owner`` e ``modifier`` são preenchidos com o usuário da requisição,
      e o que o cliente enviar neles é ignorado;
    - quem não é superusuário não cria, altera nem apaga as chaves de
      armazenamento de ``metadata``."""

    CAMPOS_DE_REGISTRO = ("ip", "user")
    CAMPOS_DE_AUDITORIA = ("owner", "modifier")
    METADATA_CHAVES_DE_ARMAZENAMENTO = ("s3_aws", "s3_cmj", "locaweb")

    link_detail_backend = serializers.SerializerMethodField()

    class Meta(DrfAutoApiSerializerMixin.Meta):
        fields = "__all__"

    def get_extra_kwargs(self):
        extra_kwargs = super().get_extra_kwargs()
        for campo in self.campos_de_auditoria():
            extra_kwargs[campo] = {**extra_kwargs.get(campo, {}), "read_only": True}
        return extra_kwargs

    def get_fields(self):
        fields = super().get_fields()
        if self.model_guarda_quem_registrou() and not self.usuario_e_superusuario():
            for campo in self.CAMPOS_DE_REGISTRO:
                fields.pop(campo, None)
        if not self.usuario_lista_o_model():
            for campo in self.relacoes_com_usuario():
                fields.pop(campo, None)
        return fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        metadata = data.get("metadata")
        if isinstance(metadata, dict) and not self.usuario_e_superusuario():
            # cópia: o dicionário original é o do próprio objeto
            data["metadata"] = self.sem_chaves_de_armazenamento(metadata)
        return data

    def create(self, validated_data):
        self.preenche_auditoria(validated_data, criando=True)
        self.preserva_armazenamento(validated_data, None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self.preenche_auditoria(validated_data, criando=False)
        self.preserva_armazenamento(validated_data, instance)
        return super().update(instance, validated_data)

    def usuario_da_requisicao(self):
        request = self.context.get("request", None)
        return getattr(request, "user", None)

    def usuario_e_superusuario(self):
        user = self.usuario_da_requisicao()
        return bool(user and user.is_superuser)

    def usuario_lista_o_model(self):
        model = self.model_do_serializer()
        user = self.usuario_da_requisicao()
        if model is None or user is None:
            return False
        return user.has_perm(f"{model._meta.app_label}.list_{model._meta.model_name}")

    def model_do_serializer(self):
        return getattr(getattr(self, "Meta", None), "model", None)

    def model_guarda_quem_registrou(self):
        model = self.model_do_serializer()
        if model is None:
            return False
        try:
            for campo in self.CAMPOS_DE_REGISTRO:
                model._meta.get_field(campo)
        except FieldDoesNotExist:
            return False
        return True

    def relacoes_com_usuario(self):
        """Campos do model que apontam para o model de usuário."""
        model = self.model_do_serializer()
        if model is None:
            return []
        return [
            field.name
            for field in model._meta.get_fields()
            if field.is_relation
            and not field.auto_created
            and field.related_model is self.user_model
        ]

    def campos_de_auditoria(self):
        """``owner`` e ``modifier`` do model, quando apontam para o usuário."""
        relacoes = self.relacoes_com_usuario()
        return [campo for campo in self.CAMPOS_DE_AUDITORIA if campo in relacoes]

    def preenche_auditoria(self, validated_data, criando):
        user = self.usuario_da_requisicao()
        if user is None or not user.is_authenticated:
            return
        for campo in self.campos_de_auditoria():
            if criando or campo == "modifier":
                validated_data[campo] = user

    def sem_chaves_de_armazenamento(self, metadata):
        return {
            chave: valor
            for chave, valor in metadata.items()
            if chave not in self.METADATA_CHAVES_DE_ARMAZENAMENTO
        }

    def preserva_armazenamento(self, validated_data, instance):
        """Na gravação por quem não é superusuário, as chaves de
        armazenamento de ``metadata`` ficam como estão no registro."""
        if "metadata" not in validated_data or self.usuario_e_superusuario():
            return
        recebido = validated_data["metadata"]
        atual = getattr(instance, "metadata", None)
        guardadas = {
            chave: valor
            for chave, valor in (atual if isinstance(atual, dict) else {}).items()
            if chave in self.METADATA_CHAVES_DE_ARMAZENAMENTO
        }
        if isinstance(recebido, dict):
            validated_data["metadata"] = {
                **self.sem_chaves_de_armazenamento(recebido),
                **guardadas,
            }
        elif guardadas:
            validated_data["metadata"] = guardadas

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
