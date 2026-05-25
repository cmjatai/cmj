from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.response import Response

from cmj.api.forms import RegistroAjusteLoaFilterSet


class RegistroAjusteLoaViewSet:
    filterset_class = RegistroAjusteLoaFilterSet

    @action(detail=False)
    def totalize_empenhos(self, request, pk=None):
        def filter_queryset():
            qs = self.filter_queryset(self.get_queryset())
            return qs

        qs = filter_queryset()
        totals = qs.aggregate(
            total_empenhado=Sum("empenhoemendaajuste_set__empenho__valor_empenhado"),
            total_liquidado=Sum("empenhoemendaajuste_set__empenho__valor_liquidado"),
            total_pago_bruto=Sum("empenhoemendaajuste_set__empenho__valor_pago_bruto"),
            total_anulado=Sum("empenhoemendaajuste_set__empenho__valor_anulado"),
        )

        return Response(totals)
