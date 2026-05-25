from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.response import Response

from cmj.api.forms import RegistroAjusteLoaFilterSet
from cmj.loa.models import Empenho


class RegistroAjusteLoaViewSet:
    filterset_class = RegistroAjusteLoaFilterSet

    @action(detail=False)
    def totalize_empenhos(self, request, pk=None):
        def filter_queryset():
            qs = self.filter_queryset(self.get_queryset())
            return qs

        qs = filter_queryset()
        empenho_ids = qs.values_list(
            "empenhoemendaajuste_set__empenho_id", flat=True
        ).distinct()
        totals = Empenho.objects.filter(id__in=empenho_ids).aggregate(
            total_empenhado=Sum("valor_empenhado"),
            total_liquidado=Sum("valor_liquidado"),
            total_pago_bruto=Sum("valor_pago_bruto"),
            total_anulado=Sum("valor_anulado"),
        )

        return Response(totals)
