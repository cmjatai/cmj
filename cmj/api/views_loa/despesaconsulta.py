import logging
from decimal import Decimal

from django.db.models import Q
from django.db.models.aggregates import Sum
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from rest_framework.fields import SerializerMethodField

from cmj.api.serializers import CmjSerializerMixin
from cmj.loa.models import (
    DespesaConsulta,
    EmendaLoaRegistroContabil,
)

logger = logging.getLogger(__name__)


class DespesaConsultaSerializer(CmjSerializerMixin):

    str_valor = SerializerMethodField()
    str_saldo = SerializerMethodField()

    class Meta(CmjSerializerMixin.Meta):
        model = DespesaConsulta

    def get_str_valor(self, obj):
        return formats.number_format(obj.valor_materia, force_grouping=True)

    def get_str_saldo(self, obj):
        valor = obj.valor_materia or Decimal("0.00")

        regs = EmendaLoaRegistroContabil.objects.filter(despesa_id=obj.id).aggregate(
            soma=Sum("valor")
        )
        saldo = valor + (regs["soma"] or Decimal("0.00"))

        return formats.number_format(saldo, force_grouping=True)


class DespesaConsultaViewSet:

    serializer_class = DespesaConsultaSerializer

    @action(detail=False)
    def search(self, request, *args, **kwargs):

        def filter_queryset(qs):
            ano = request.GET.get("ano", None)
            query = request.GET.get("q", "")
            query = query.split(" ")

            q = Q()

            for termo in query:
                q &= (
                    Q(codigo__unaccent__icontains=termo)
                    | Q(especificacao__unaccent__icontains=termo)
                    | Q(cod_orgao__unaccent__icontains=termo)
                    | Q(esp_orgao__unaccent__icontains=termo)
                    | Q(cod_unidade__unaccent__icontains=termo)
                    | Q(esp_unidade__unaccent__icontains=termo)
                    | Q(cod_natureza__unaccent__icontains=termo)
                    | Q(esp_natureza__unaccent__icontains=termo)
                    | Q(cod_fonte__unaccent__icontains=termo)
                )

            qs = qs.filter(loa__ano=ano)
            if query:
                qs = qs.filter(q)

            return qs.order_by(
                "cod_orgao", "cod_unidade", "codigo", "cod_natureza", "cod_fonte"
            )

        self.filter_queryset = filter_queryset

        return self.list(request, *args, **kwargs)
