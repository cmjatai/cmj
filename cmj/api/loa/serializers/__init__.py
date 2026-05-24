from decimal import Decimal

from django.db.models import Sum
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.fields import SerializerMethodField

from cmj.api.serializers import CmjSerializerMixin
from cmj.loa.models import (
    ArquivoPrestacaoContaRegistro,
    EmendaLoa,
    PrestacaoContaRegistro,
    RegistroAjusteLoa,
)
from cmj.loa.models.m_financeiro_execucao import Empenho


class EmendaLoaSearchSerializer(CmjSerializerMixin):

    str_valor = SerializerMethodField()
    str_parlamentares = SerializerMethodField()

    finalidade = SerializerMethodField()

    str_fase = SerializerMethodField()

    class Meta(CmjSerializerMixin.Meta):
        model = EmendaLoa

    def get_finalidade(self, obj):
        return obj.finalidade_format

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


class RegistroAjusteLoaSerializer(CmjSerializerMixin):
    str_valor = serializers.CharField(read_only=True)

    # crie o campo valor como DecimalField chamanado método para calcular
    valor = serializers.SerializerMethodField()
    valor_por_parlamentar = serializers.SerializerMethodField()

    soma_valor_empenhado = serializers.SerializerMethodField()
    soma_valor_liquidado = serializers.SerializerMethodField()
    soma_valor_pago_bruto = serializers.SerializerMethodField()
    soma_valor_anulado = serializers.SerializerMethodField()

    class Meta(CmjSerializerMixin.Meta):
        model = RegistroAjusteLoa

    def get_soma_valor_empenhado(self, obj):
        return obj.empenhoemendaajuste_set.aggregate(
            total=Sum("empenho__valor_empenhado")
        )["total"] or Decimal("0.00")

    def get_soma_valor_liquidado(self, obj):
        return obj.empenhoemendaajuste_set.aggregate(
            total=Sum("empenho__valor_liquidado")
        )["total"] or Decimal("0.00")

    def get_soma_valor_pago_bruto(self, obj):
        return obj.empenhoemendaajuste_set.aggregate(
            total=Sum("empenho__valor_pago_bruto")
        )["total"] or Decimal("0.00")

    def get_soma_valor_anulado(self, obj):
        return obj.empenhoemendaajuste_set.aggregate(
            total=Sum("empenho__valor_anulado")
        )["total"] or Decimal("0.00")

    def get_valor_por_parlamentar(self, obj):
        valores = {}
        for registro in obj.registroajusteloaparlamentar_set.all():
            parlamentar = registro.parlamentar
            if parlamentar:
                valores[parlamentar.id] = valores.get(parlamentar.id, 0) + (
                    registro.valor or Decimal("0.00")
                )
        return valores

    def get_valor(self, obj):
        total = obj.registroajusteloaparlamentar_set.order_by("parlamentar").aggregate(
            total=Sum("valor")
        )
        return total["total"] if total["total"] else 0


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

    valor_inicial_por_parlamentar = serializers.SerializerMethodField()
    has_ajustes = serializers.BooleanField(read_only=True)

    soma_valor_empenhado = serializers.SerializerMethodField()
    soma_valor_liquidado = serializers.SerializerMethodField()
    soma_valor_pago_bruto = serializers.SerializerMethodField()
    soma_valor_anulado = serializers.SerializerMethodField()

    class Meta(CmjSerializerMixin.Meta):
        model = EmendaLoa

    def get_soma_valor_empenhado(self, obj):
        return obj.empenhoemendaajuste_set.aggregate(
            total=Sum("empenho__valor_empenhado")
        )["total"] or Decimal("0.00")

    def get_soma_valor_liquidado(self, obj):
        return obj.empenhoemendaajuste_set.aggregate(
            total=Sum("empenho__valor_liquidado")
        )["total"] or Decimal("0.00")

    def get_soma_valor_pago_bruto(self, obj):
        return obj.empenhoemendaajuste_set.aggregate(
            total=Sum("empenho__valor_pago_bruto")
        )["total"] or Decimal("0.00")

    def get_soma_valor_anulado(self, obj):
        return obj.empenhoemendaajuste_set.aggregate(
            total=Sum("empenho__valor_anulado")
        )["total"] or Decimal("0.00")

    def get_valor_inicial_por_parlamentar(self, obj):
        valores = {}
        for registro in obj.emendaloaparlamentar_set.all():
            parlamentar = registro.parlamentar
            if parlamentar:
                valores[parlamentar.id] = valores.get(parlamentar.id, 0) + (
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
