import logging

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from sapl.parlamentares.models import Legislatura, SessaoLegislativa
from sapl.relatorios.forms import (
    RelatorioPresencaSessaoFilterSet,
)
from sapl.relatorios.view_reports.mixins import RelatorioMixin
from sapl.sessao.models import (
    JustificativaAusencia,
    PresencaOrdemDia,
    SessaoPlenaria,
    SessaoPlenariaPresenca,
    TipoSessaoPlenaria,
)
from sapl.utils import parlamentares_ativos, show_results_filter_set

logger = logging.getLogger(__name__)


class View(RelatorioMixin, FilterView):
    model = SessaoPlenaria
    filterset_class = RelatorioPresencaSessaoFilterSet

    data_init = {}

    def get_filterset_kwargs(self, filterset_class):
        super().get_filterset_kwargs(filterset_class)
        self.data_init = kwargs = {"data": self.request.GET or None}

        if kwargs["data"] and "legislatura_atual" in kwargs["data"]:
            kwargs["data"] = {"tipo": "", "autoria__autor": ""}
            la = Legislatura.cache_legislatura_atual()
            kwargs["data"]["data_apresentacao_0"] = formats.date_format(
                la["data_inicio"], "d/m/Y"
            )
            kwargs["data"]["data_apresentacao_1"] = formats.date_format(
                la["data_fim"], "d/m/Y"
            )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "title_pdf": _("PortalCMJ - Presença por Sessão"),
            }
        )
        context["title"] = _("Presença dos parlamentares nas sessões")

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        cd = self.filterset.form.cleaned_data
        if (
            not cd["data_inicio"]
            and not cd["sessao_legislativa"]
            and not cd["legislatura"]
        ):
            msg = _(
                "Formulário inválido! Preencha pelo menos algum dos campos Período, Legislatura ou Sessão Legislativa."
            )
            messages.error(self.request, msg)
            return context

        # Caso a data tenha sido preenchida, verifica se foi preenchida
        # corretamente
        if self.request.GET.get("data_inicio_0") and not self.request.GET.get(
            "data_inicio_1"
        ):
            msg = _("Formulário inválido! Preencha a data do Período Final.")
            messages.error(self.request, msg)
            return context

        if not self.request.GET.get("data_inicio_0") and self.request.GET.get(
            "data_inicio_1"
        ):
            msg = _("Formulário inválido! Preencha a data do Período Inicial.")
            messages.error(self.request, msg)
            return context

        param0 = {}

        legislatura_pk = self.request.GET.get("legislatura")
        if legislatura_pk:
            param0["sessao_plenaria__legislatura_id"] = legislatura_pk
            legislatura = Legislatura.objects.get(id=legislatura_pk)
            context["legislatura"] = legislatura

        sessao_legislativa_pk = self.request.GET.get("sessao_legislativa")
        if sessao_legislativa_pk:
            param0["sessao_plenaria__sessao_legislativa_id"] = sessao_legislativa_pk
            sessao_legislativa = SessaoLegislativa.objects.get(id=sessao_legislativa_pk)
            context["sessao_legislativa"] = sessao_legislativa

        tipo_sessao_plenaria_pk = self.request.GET.get("tipo")
        context["tipo"] = ""
        if tipo_sessao_plenaria_pk:
            param0["sessao_plenaria__tipo_id"] = tipo_sessao_plenaria_pk
            context["tipo"] = TipoSessaoPlenaria.objects.get(id=tipo_sessao_plenaria_pk)

        _range = []

        if (
            ("data_inicio_0" in self.request.GET)
            and self.request.GET["data_inicio_0"]
            and ("data_inicio_1" in self.request.GET)
            and self.request.GET["data_inicio_1"]
        ):
            where = context["object_list"].query.where
            _range = where.children[0].rhs

        elif legislatura_pk and not sessao_legislativa_pk:
            _range = [legislatura.data_inicio, legislatura.data_fim]

        elif sessao_legislativa_pk:
            _range = [sessao_legislativa.data_inicio, sessao_legislativa.data_fim]

        param0.update({"sessao_plenaria__data_inicio__range": _range})

        # Parlamentares com Mandato no intervalo de tempo (Ativos)
        parlamentares_qs = parlamentares_ativos(_range[0], _range[1]).order_by(
            "nome_parlamentar"
        )
        parlamentares_id = parlamentares_qs.values_list("id", flat=True)

        # Presenças de cada Parlamentar em Sessões
        presenca_sessao = (
            SessaoPlenariaPresenca.objects.filter(**param0)
            .values_list("parlamentar_id")
            .annotate(sessao_count=Count("id"))
        )

        # Presenças de cada Ordem do Dia
        presenca_ordem = (
            PresencaOrdemDia.objects.filter(**param0)
            .values_list("parlamentar_id")
            .annotate(sessao_count=Count("id"))
        )

        # Ausencias justificadas
        ausencia_justificadas = (
            JustificativaAusencia.objects.filter(**param0, ausencia=2)
            .values_list("parlamentar_id")
            .annotate(sessao_count=Count("id"))
        )

        total_ordemdia = (
            PresencaOrdemDia.objects.filter(**param0)
            .distinct("sessao_plenaria__id")
            .order_by("sessao_plenaria__id")
            .count()
        )

        total_sessao = context["object_list"].count()

        username = self.request.user.username

        context["exibir_somente_titular"] = (
            self.request.GET.get("exibir_somente_titular") == "on"
        )
        context["exibir_somente_ativo"] = (
            self.request.GET.get("exibir_somente_ativo") == "on"
        )

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

            if (
                not context["exibir_somente_titular"]
                and not context["exibir_somente_ativo"]
            ):
                parlamentar = {
                    "parlamentar": p,
                    "titular": m.titular if m else False,
                    "sessao_porc": 0,
                    "ordemdia_porc": 0,
                }
            elif (
                context["exibir_somente_titular"]
                and not context["exibir_somente_ativo"]
            ):
                if m and m.titular:
                    parlamentar = {
                        "parlamentar": p,
                        "titular": m.titular if m else False,
                        "sessao_porc": 0,
                        "ordemdia_porc": 0,
                    }
                else:
                    continue
            elif (
                not context["exibir_somente_titular"]
                and context["exibir_somente_ativo"]
            ):
                if p.ativo:
                    parlamentar = {
                        "parlamentar": p,
                        "titular": m.titular if m else False,
                        "sessao_porc": 0,
                        "ordemdia_porc": 0,
                    }
                else:
                    continue
            elif context["exibir_somente_titular"] and context["exibir_somente_ativo"]:
                if m and m.titular and p.ativo:
                    parlamentar = {
                        "parlamentar": p,
                        "titular": m.titular if m else False,
                        "sessao_porc": 0,
                        "ordemdia_porc": 0,
                    }
                else:
                    continue
            else:
                continue

            try:
                logger.debug(
                    f"user={username}. Tentando obter presença do parlamentar (pk={p.id})."
                )
                sessao_count = presenca_sessao.get(parlamentar_id=p.id)[1]
            except ObjectDoesNotExist as e:
                logger.error(
                    f"user={username}. Erro ao obter presença do parlamentar (pk={p.id}). Definido como 0. {str(e)}"
                )
                sessao_count = 0
            try:
                # Presenças de cada Ordem do Dia
                logger.info(
                    f"user={username}. Tentando obter PresencaOrdemDia para o parlamentar pk={p.id}."
                )
                ordemdia_count = presenca_ordem.get(parlamentar_id=p.id)[1]
            except ObjectDoesNotExist:
                logger.error(
                    f"user={username}. Erro ao obter PresencaOrdemDia para o parlamentar pk={p.id}. Definido como 0."
                )
                ordemdia_count = 0
            try:
                logger.debug(
                    f"user={username}. Tentando obter ausência justificada do parlamentar (pk={p.id})."
                )
                ausencia_justificadas_count = ausencia_justificadas.get(
                    parlamentar_id=p.id
                )[1]
            except ObjectDoesNotExist as e:
                logger.error(
                    f"user={username}. Erro ao obter ausência do parlamentar (pk={p.id}). Definido como 0. {str(e)}"
                )
                ausencia_justificadas_count = 0

            ausencia_count = total_sessao - sessao_count if total_sessao else 0
            ausencia_porc = (
                round(100 * (1 - sessao_count / total_sessao), 2) if total_sessao else 0
            )
            # # porcentagem do total de ausencias
            # ausencia_justificadas_porc = round(100 * ausencias_justificadas_count / ausencia_count, 2)\
            #     if ausencia_count else 0

            # porcentagem do total de sessoes
            ausencia_justificadas_porc = (
                round(100 * ausencia_justificadas_count / total_sessao, 2)
                if total_sessao
                else 0
            )

            parlamentar.update(
                {
                    "sessao_count": sessao_count,
                    "ordemdia_count": ordemdia_count,
                    "ausencia_count": ausencia_count,
                    "ausencia_porc": ausencia_porc,
                    "ausencia_justificada_count": ausencia_justificadas_count,
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
            f"{self.request.GET['data_inicio_0']} - {self.request.GET['data_inicio_1']}"
        )
        context["sessao_legislativa"] = ""
        context["legislatura"] = ""
        context["exibir_ordem"] = self.request.GET.get("exibir_ordem_dia") == "on"

        if sessao_legislativa_pk:
            context["sessao_legislativa"] = SessaoLegislativa.objects.get(
                id=sessao_legislativa_pk
            )
        if legislatura_pk:
            context["legislatura"] = Legislatura.objects.get(id=legislatura_pk)
        # =====================================================================
        qr = self.request.GET.copy()
        context["filter_url"] = ("&" + qr.urlencode()) if len(qr) > 0 else ""

        context["show_results"] = show_results_filter_set(qr)

        return context
