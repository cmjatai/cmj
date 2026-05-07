import logging

from django.contrib import messages
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from sapl.parlamentares.models import Legislatura
from sapl.relatorios.forms import (
    RelatorioPresencaSessaoFilterSet,
)
from sapl.relatorios.view_reports.mixins import RelatorioMixin
from sapl.sessao.models import (
    JustificativaAusencia,
    PresencaOrdemDia,
    SessaoPlenaria,
    SessaoPlenariaPresenca,
)
from sapl.utils import parlamentares_ativos, show_results_filter_set

logger = logging.getLogger(__name__)


class View(RelatorioMixin, FilterView):
    model = SessaoPlenaria
    filterset_class = RelatorioPresencaSessaoFilterSet

    data_init = {}

    def get_filterset_kwargs(self, filterset_class):

        super().get_filterset_kwargs(filterset_class)
        self.data_init = kwargs = {"data": self.request.GET or {}}

        if not kwargs["data"] or "legislatura" not in kwargs["data"]:
            legislatura_atual = Legislatura.cache_legislatura_atual()
            kwargs["data"]["legislatura"] = legislatura_atual["id"]
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "title_pdf": _("PortalCMJ - Presença dos parlamentares nas sessões"),
            }
        )
        context["title"] = _("Presença dos parlamentares nas sessões")

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        sessoes_filtradas = context["object_list"]

        cd = self.filterset.form.cleaned_data

        if not sessoes_filtradas.exists():
            messages.error(
                self.request, _("Nenhuma sessão encontrada para os filtros aplicados.")
            )
            return context

        legislatura = cd.get("legislatura", "")
        context["legislatura"] = legislatura or ""

        sessao_legislativa = cd.get("sessao_legislativa", "")
        context["sessao_legislativa"] = sessao_legislativa or ""

        tipo_sessao_plenaria = cd.get("tipo", "")
        context["tipo"] = tipo_sessao_plenaria or ""

        data_inicio = cd.get("data_inicio", None)
        context["data_inicio"] = data_inicio

        d_ini_base = (
            sessao_legislativa.data_inicio
            if sessao_legislativa
            else legislatura.data_inicio
        )
        d_fim_base = (
            sessao_legislativa.data_fim if sessao_legislativa else legislatura.data_fim
        )

        _range = (
            data_inicio and data_inicio.start or d_ini_base,
            data_inicio and data_inicio.stop or d_fim_base,
        )

        # Parlamentares com Mandato no intervalo de tempo
        parlamentares_qs = parlamentares_ativos(_range[0], _range[1]).order_by(
            "nome_parlamentar"
        )
        parlamentares_id = parlamentares_qs.values_list("id", flat=True)

        params = {
            "sessao_plenaria__in": sessoes_filtradas,
            "parlamentar_id__in": parlamentares_id,
        }

        # Presenças de cada Parlamentar em Sessões
        presenca_sessao = (
            SessaoPlenariaPresenca.objects.filter(**params)
            .values_list("parlamentar_id")
            .order_by("parlamentar_id")
            .annotate(sessao_count=Count("id"))
        )

        # Presenças de cada Ordem do Dia
        presenca_ordem = (
            PresencaOrdemDia.objects.filter(**params)
            .values_list("parlamentar_id")
            .order_by("parlamentar_id")
            .annotate(sessao_count=Count("id"))
        )

        # Ausencias justificadas
        aus_just = (
            JustificativaAusencia.objects.filter(**params, ausencia=2)
            .values_list("parlamentar_id")
            .order_by("parlamentar_id")
            .annotate(sessao_count=Count("id"))
        )

        total_ordemdia = (
            PresencaOrdemDia.objects.filter(
                sessao_plenaria__in=sessoes_filtradas,
            )
            .distinct("sessao_plenaria__id")
            .order_by("sessao_plenaria__id")
            .count()
        )

        total_sessao = context["object_list"].count()

        # Completa o dicionario as informacoes parlamentar/sessao/ordem
        parlamentares_presencas = []
        for p in parlamentares_qs:
            parlamentar = {}
            m = p.mandato_set.filter(
                Q(data_inicio_mandato__lte=_range[0], data_fim_mandato__gte=_range[1])
                | Q(data_inicio_mandato__lte=_range[0], data_fim_mandato__isnull=True)
                | Q(data_inicio_mandato__gte=_range[0], data_fim_mandato__lte=_range[1])
                |
                # mandato suplente
                Q(data_inicio_mandato__gte=_range[0], data_fim_mandato__lte=_range[1])
            )

            m = m.last()

            parlamentar = {
                "parlamentar": p,
                "titular": m.titular if m else False,
                "sessao_porc": 0,
                "ordemdia_porc": 0,
            }

            sessao_count = presenca_sessao.filter(parlamentar_id=p.id).first()
            sessao_count = sessao_count[1] if sessao_count else 0

            ordemdia_count = presenca_ordem.filter(parlamentar_id=p.id).first()
            ordemdia_count = ordemdia_count[1] if ordemdia_count else 0

            aus_jus_count = aus_just.filter(parlamentar_id=p.id).first()
            aus_jus_count = aus_jus_count[1] if aus_jus_count else 0

            ausencia_count = total_sessao - sessao_count if total_sessao else 0
            ausencia_porc = (
                round(100 * (1 - sessao_count / total_sessao), 2) if total_sessao else 0
            )
            # # porcentagem do total de ausencias
            # ausencia_justificadas_porc = round(100 * ausencias_justificadas_count / ausencia_count, 2)\
            #     if ausencia_count else 0

            # porcentagem do total de sessoes
            ausencia_justificadas_porc = (
                round(100 * aus_jus_count / total_sessao, 2) if total_sessao else 0
            )

            parlamentar.update(
                {
                    "sessao_count": sessao_count,
                    "ordemdia_count": ordemdia_count,
                    "ausencia_count": ausencia_count,
                    "ausencia_porc": ausencia_porc,
                    "ausencia_justificada_count": aus_jus_count,
                    "ausencia_justificadas_porc": ausencia_justificadas_porc,
                }
            )

            if total_sessao != 0:
                parlamentar.update(
                    {"sessao_porc": round(sessao_count * 100 / total_sessao, 2)}
                )
            if total_ordemdia != 0:
                parlamentar.update(
                    {"ordemdia_porc": round(ordemdia_count * 100 / total_ordemdia, 2)}
                )

            parlamentares_presencas.append(parlamentar)

        context["date_range"] = _range
        context["total_ordemdia"] = total_ordemdia
        context["total_sessao"] = context["object_list"].count()
        context["parlamentares"] = parlamentares_presencas
        context["periodo"] = (
            f"{_range[0].strftime('%d/%m/%Y') if _range and _range[0] else '...'} - "
            f"{_range[1].strftime('%d/%m/%Y') if _range and _range[1] else '...'}"
        )

        context["sessao_legislativa"] = sessao_legislativa or "Todas"
        context["tipo"] = tipo_sessao_plenaria or "Todos"
        qr = self.request.GET.copy()
        context["filter_url"] = ("&" + qr.urlencode()) if len(qr) > 0 else ""

        context["show_results"] = show_results_filter_set(qr)

        return context
