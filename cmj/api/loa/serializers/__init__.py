from decimal import Decimal

from django.db.models import Count, Exists, IntegerField, OuterRef, Prefetch, Subquery
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.fields import SerializerMethodField

from cmj.api.serializers import CmjSerializerMixin
from cmj.loa.models import (
    ArquivoPrestacaoContaRegistro,
    EmendaLoa,
    EmendaLoaParlamentar,
    PrestacaoContaRegistro,
    RegistroAjusteLoa,
    RegistroAjusteLoaParlamentar,
)
from cmj.loa.models.m_financeiro_execucao import Empenho


def emendas_para_serializar(queryset):
    """Emendas com o que os serializers leem já carregado, para o custo não
    crescer com a quantidade de itens (LOA-PCC-080)."""
    ajustes_da_emenda = RegistroAjusteLoa.emendaloa.through.objects.filter(
        emendaloa_id=OuterRef("pk")
    )
    return (
        queryset.select_related(
            "loa", "unidade", "entidade__tipo_entidade", "bairro", "materia__tipo"
        )
        .prefetch_related(
            "parlamentares",
            Prefetch(
                "emendaloaparlamentar_set",
                queryset=EmendaLoaParlamentar.objects.select_related("parlamentar"),
            ),
            "empenhoemendaajuste_set__empenho",
        )
        .annotate(
            # os dois que EmendaLoa.has_ajustes e valor_computado consultariam
            ann_has_ajustes=Exists(
                RegistroAjusteLoaParlamentar.objects.filter(
                    registro__emendaloa=OuterRef("pk")
                )
            ),
            ann_num_ajustes=Coalesce(
                Subquery(
                    ajustes_da_emenda.order_by()
                    .values("emendaloa_id")
                    .annotate(total=Count("pk"))
                    .values("total"),
                    output_field=IntegerField(),
                ),
                0,
            ),
        )
    )


def ajustes_para_serializar(queryset):
    """Registros de ajuste com o que os serializers leem já carregado
    (LOA-PCC-080). As emendas vinculadas vêm prontas para o ``expand``."""
    return queryset.select_related(
        "oficio_ajuste_loa", "unidade", "entidade"
    ).prefetch_related(
        "registroajusteloaparlamentar_set",
        "parlamentares_valor",
        "empenhoemendaajuste_set__empenho",
        Prefetch(
            "emendaloa", queryset=emendas_para_serializar(EmendaLoa.objects.all())
        ),
    )


class SomaDosEmpenhosMixin:
    """As quatro somas de empenhos de um item saem de um cálculo só."""

    def get_soma_empenhos(self, obj):
        if not hasattr(obj, "_soma_dos_empenhos"):
            obj._soma_dos_empenhos = (
                obj.empenhoemendaajuste_set.aggregate_sum_dos_empenhos()
            )
        return obj._soma_dos_empenhos

    def get_soma_valor_empenhado(self, obj):
        return self.get_soma_empenhos(obj)["valor_empenhado"] or Decimal("0.00")

    def get_soma_valor_liquidado(self, obj):
        return self.get_soma_empenhos(obj)["valor_liquidado"] or Decimal("0.00")

    def get_soma_valor_pago_bruto(self, obj):
        return self.get_soma_empenhos(obj)["valor_pago_bruto"] or Decimal("0.00")

    def get_soma_valor_anulado(self, obj):
        return self.get_soma_empenhos(obj)["valor_anulado"] or Decimal("0.00")


class OcultaCamposInternosDaEmendaMixin:
    """LOA-LST-091: ``owner``, ``metadata`` e ``search`` só para quem pode
    editar a emenda em alguma fase."""

    CAMPOS_INTERNOS = ("owner", "metadata", "search")

    def get_fields(self):
        # quem não vê esses campos em emenda nenhuma não os tem no serializer:
        # assim eles também não valem como filtro nem como ordenação
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not EmendaLoa.service.pode_ver_campos_internos(user):
            for campo in self.CAMPOS_INTERNOS:
                fields.pop(campo, None)
        return fields

    def to_representation(self, obj):
        data = super().to_representation(obj)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not EmendaLoa.service.ve_campos_internos(user, obj):
            for campo in self.CAMPOS_INTERNOS:
                data.pop(campo, None)
        return data


class EmendaLoaSearchSerializer(OcultaCamposInternosDaEmendaMixin, CmjSerializerMixin):

    str_valor = SerializerMethodField()
    str_parlamentares = SerializerMethodField()

    finalidade = SerializerMethodField()

    str_fase = SerializerMethodField()

    agrupamento = SerializerMethodField()

    class Meta(CmjSerializerMixin.Meta):
        model = EmendaLoa

    def get_finalidade(self, obj):
        return obj.finalidade_format

    def get_agrupamento(self, obj):
        """Agrupamento em que a emenda está, ou None (LOA-AGR-096).

        Nome e detalhe do agrupamento já são públicos (LOA-AGR-001).
        """
        vinculo = getattr(obj, "agrupamentoemendaloa", None)
        if vinculo is None:
            return None
        agrupamento = vinculo.agrupamento
        return {
            "id": agrupamento.id,
            "nome": agrupamento.nome,
            "link_detail_backend": reverse(
                "cmj.loa:agrupamento_detail", kwargs={"pk": agrupamento.id}
            ),
        }

    def get_str_fase(self, obj):
        return obj.get_fase_display()

    def get_str_valor(self, obj):
        return formats.number_format(obj.valor, force_grouping=True)

    def get_str_parlamentares(self, obj):
        elps = obj.emendaloaparlamentar_set.all()

        r = []
        for elp in elps:
            r.append(str(elp))
        return r


class RegistroAjusteLoaSerializer(SomaDosEmpenhosMixin, CmjSerializerMixin):
    str_valor = serializers.CharField(read_only=True)

    str_valor_computado = serializers.CharField(
        read_only=True,
    )
    valor_computado = serializers.FloatField(read_only=True)

    # crie o campo valor como DecimalField chamanado método para calcular
    valor = serializers.SerializerMethodField()
    valor_por_parlamentar = serializers.SerializerMethodField()

    soma_valor_empenhado = serializers.SerializerMethodField()
    soma_valor_liquidado = serializers.SerializerMethodField()
    soma_valor_pago_bruto = serializers.SerializerMethodField()
    soma_valor_anulado = serializers.SerializerMethodField()

    class Meta(CmjSerializerMixin.Meta):
        model = RegistroAjusteLoa

    def get_valor_por_parlamentar(self, obj):
        valores = {}
        valor_computado = obj.valor_computado
        for registro in obj.registroajusteloaparlamentar_set.all():
            parlamentar_id = registro.parlamentar_id
            if parlamentar_id:
                if valor_computado:
                    valores[parlamentar_id] = valores.get(parlamentar_id, 0) + (
                        registro.valor or Decimal("0.00")
                    )
                else:
                    valores[parlamentar_id] = Decimal("0.00")
        return valores

    def get_valor(self, obj):
        # a soma das partes; .all() aproveita o prefetch
        partes = [
            registro.valor
            for registro in obj.registroajusteloaparlamentar_set.all()
            if registro.valor is not None
        ]
        total = sum(partes, Decimal("0.00")) if partes else None
        return total if total else 0


class EmendaLoaSerializer(
    SomaDosEmpenhosMixin, OcultaCamposInternosDaEmendaMixin, CmjSerializerMixin
):

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

    valor_inicial_por_parlamentar = serializers.SerializerMethodField()
    has_ajustes = serializers.BooleanField(read_only=True)

    soma_valor_empenhado = serializers.SerializerMethodField()
    soma_valor_liquidado = serializers.SerializerMethodField()
    soma_valor_pago_bruto = serializers.SerializerMethodField()
    soma_valor_anulado = serializers.SerializerMethodField()

    class Meta(CmjSerializerMixin.Meta):
        model = EmendaLoa

    def get_valor_inicial_por_parlamentar(self, obj):
        valores = {}
        for registro in obj.emendaloaparlamentar_set.all():
            parlamentar_id = registro.parlamentar_id
            if parlamentar_id:
                valores[parlamentar_id] = valores.get(parlamentar_id, 0) + (
                    registro.valor or Decimal("0.00")
                )
        return valores

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


class ArquivoPrestacaoContaRegistroSerializer(CmjSerializerMixin):

    class Meta(CmjSerializerMixin.Meta):
        model = ArquivoPrestacaoContaRegistro


class PrestacaoContaRegistroSerializer(CmjSerializerMixin):

    arquivos = ArquivoPrestacaoContaRegistroSerializer(
        many=True,
        read_only=True,
        source="arquivoprestacaocontaregistro_set",
    )

    class Meta(CmjSerializerMixin.Meta):
        model = PrestacaoContaRegistro


class EmpenhoSerializer(CmjSerializerMixin):

    total_registros = serializers.IntegerField(
        source="empenhoemendaajuste_set.count", read_only=True
    )

    class Meta(CmjSerializerMixin.Meta):
        model = Empenho
