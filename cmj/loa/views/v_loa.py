from decimal import ROUND_DOWN, Decimal

from django.db.models import Exists, OuterRef, Q
from django.db.models.aggregates import Sum
from django.http import HttpResponse, HttpResponseBadRequest
from django.http.response import Http404
from django.shortcuts import redirect
from django.template import loader
from django.urls.base import reverse, reverse_lazy
from django.utils import formats, timezone
from django.utils.decorators import classonlymethod
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError as DRFValidationError

from cmj.api.forms import EmendaLoaFilterSet, RegistroAjusteLoaFilterSet
from cmj.loa.forms.f_loa import LoaForm
from cmj.loa.models import (
    EmendaLoa,
    EmendaLoaParlamentar,
    Loa,
    RegistroAjusteLoaParlamentar,
)
from cmj.loa.models.m_ajusteloa import RegistroAjusteLoa
from cmj.loa.models.m_prestacaoconta import PrestacaoContaRegistro
from cmj.loa.services.s_emendaloa import EmendaLoaService
from cmj.loa.services.s_prestacaoconta import PrestacaoContaService
from cmj.loa.services.s_visibilidade import VisibilidadeLoaService
from cmj.loa.views.v_mixins import LoaContextDataMixin
from cmj.mixins import GoogleRecapthaViewMixin
from cmj.search.views import InfoFilterMixin
from cmj.utils import quantize
from sapl.crud.base import RP_DETAIL, RP_LIST, Crud


class LoaCrud(Crud):
    model = Loa
    public = [RP_LIST, RP_DETAIL]
    ordered_list = False
    frontend = Loa._meta.app_label

    @classonlymethod
    def get_urls(cls):
        urls = super().get_urls()
        from django.urls import path

        def redirect_to_latest_loa(request):
            try:
                # LOA-CRUD-065: emenda transformada em coletiva (fase -10) não conta
                latest_loa = Loa.objects.filter(
                    publicado=True, emendaloa_set__fase__gt=0
                ).latest("ano")
                return redirect("cmj.loa:prestacaoconta_detail", pk=latest_loa.pk)
            except Loa.DoesNotExist:
                raise Http404(_("Nenhuma LOA publicada encontrada."))

        def despesas_espelho(request, pk):
            try:
                loa = Loa.objects.get(pk=pk, publicado=True)
            except Loa.DoesNotExist:
                raise Http404(_("LOA não encontrada."))
            template = loader.get_template("loa/despesas_espelho.html")
            context = {
                "object": loa,
                "root_pk": pk,
                "title": f"Espelho das Despesas <small>({loa})</small>",
                "path": " container-loa despesas-espelho",
                "subnav_template_name": "loa/subnav_loa_em_tramitacao.yaml",
            }
            return HttpResponse(template.render(context, request))

        urls = [
            path("/atual", redirect_to_latest_loa, name="loa_atual"),
            path("/<int:pk>/despesas", despesas_espelho, name="loa_despesas_espelho"),
            path(
                "/<int:pk>/prestacaoconta",
                LoaCrud.PrestacaoContaView.as_view(),
                name="prestacaoconta_detail",
            ),
        ] + urls
        return urls

    class BaseMixin(LoaContextDataMixin, Crud.BaseMixin):

        @property
        def list_field_names(self):
            list_field_names = [
                "ano",
                "receita_corrente_liquida",
                ("disp_total", "perc_disp_total"),
                ("disp_saude", "perc_disp_saude"),
                ("disp_diversos", "perc_disp_diversos"),
            ]

            if not self.request.user.is_anonymous:
                list_field_names.append("publicado")
            return list_field_names

        @property
        def verbose_name(self):
            return _("Lei Orçamentária Anual")

        @property
        def verbose_name_plural(self):
            return _("Leis Orçamentárias Anuais")

        @property
        def list_url(self):
            url = super().list_url
            if self.request.user.is_anonymous:
                c = Loa.objects.filter(publicado=True).count()
                return url if c > 1 else ""
            return url

    class ListView(Crud.ListView):
        ordered_list = False
        paginate_by = 4

        def get(self, request, *args, **kwargs):
            response = super().get(request, *args, **kwargs)

            if self.object_list.count() == 1:
                loa = self.object_list.first()
                return redirect(
                    to=reverse_lazy("cmj.loa:loa_detail", kwargs={"pk": loa.pk})
                )
            return response

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} loa-list"
            context["type_pagination"] = "pagination-static"
            return context

        def get_queryset(self):
            qs = super().get_queryset()

            u = self.request.user

            qsp = qs.filter(publicado=True)
            if u.is_anonymous:
                return qsp

            if u.has_perm("loa.emendaloa_full_editor"):
                return qs

            if u.operadorautor_set.exists():
                qs = qs.filter(
                    Q(materia__normajuridica__isnull=True) | Q(publicado=True)
                ).distinct()
                return qs

            return qsp

        def hook_header_perc_disp_total(self):
            return ""

        def hook_header_perc_disp_saude(self):
            return ""

        def hook_header_perc_disp_diversos(self):
            return ""

        def hook_receita_corrente_liquida(self, *args, **kwargs):
            l = args[0]
            if l.ano < 2023:
                return " - ", args[2]

            ano_atual = timezone.now().year

            rcl_previa = formats.number_format(l.rcl_previa, force_grouping=True)

            if l.ano > ano_atual:
                frase = (
                    "Processo Legislativo em andamento"
                    if not l.materia or not l.materia.normajuridica()
                    else "LOA Aprovada"
                )
                return (
                    f"""
                    {rcl_previa}
                    <small>
                        <small>
                            <em class="text-orange"><strong>{frase}</strong></em>
                            <em>RCL referente ao ano anterior ao Projeto da LOA</em>
                        </small>
                    </small>
                """,
                    "",
                )

            if l.ano == ano_atual:
                return (
                    f"""
                    {args[1]}
                    <small class="text-gray">
                        <small>
                            <em>LOA em fase de Execução</em>
                            <em>RCL referente ao ano anterior à Execução</em>
                        </small>
                    </small>
                """,
                    "",
                )

            return (
                f"""
                {args[1]}
                <small class="text-gray">
                    <small>
                        <em>LOA executada em {l.ano}</em>
                        <em>RCL referente ao ano anterior à Execução</em>
                    </small>
                </small>
            """,
                "",
            )

        # def hook_header_receita_corrente_liquida(self):
        #     return 'Receita Corrente Líquida - RCL (R$)<br><small class="text-gray">RCL Referente ao ano anterior.</small>'

        def hook_ano(self, *args, **kwargs):
            l = args[0]
            if l.materia and l.materia.normajuridica():
                return (
                    f"""
                <a href="{args[2]}" title="Detalhes do Cadastro do Orçamento Impositivo">LOA {args[1]}</a><br>
                <div class="btn-group" role="group">
                    <a class="btn btn-sm btn-outline-primary" href="/loa/{l.id}/prestacaoconta" title="Prestação de Contas"><i class="fas fa-hand-holding-usd"></i></a>
                </div>
                """,
                    "",
                )
            return (
                f"""
                <a href="{args[2]}" title="Detalhes do Cadastro do Orçamento Impositivo">LOA {args[1]}</a><br>
                <a class="btn btn-sm btn-primary" href="/loa/{l.id}/emendaloa" title="Emendas à LOA em Elaboração"><i class="fas fa-clipboard-list"></i></a>
                """,
                "",
            )

        def hook_perc_disp_total(self, *args, **kwargs):
            l = args[0]
            return f" <em>({l.perc_disp_total:3.1f}%)</em>", ""

        def hook_perc_disp_saude(self, *args, **kwargs):
            l = args[0]
            return f" <em>({l.perc_disp_saude:3.1f}%)</em>", ""

        def hook_perc_disp_diversos(self, *args, **kwargs):
            l = args[0]
            return f" <em>({l.perc_disp_diversos:3.1f}%)</em>", ""

    class CreateView(Crud.CreateView):
        form_class = LoaForm

        def form_invalid(self, form):
            r = Crud.CreateView.form_invalid(self, form)

            err_materia = form.errors.get("materia", None)
            if err_materia:
                err_materia = (
                    "Já existe Loa vinculada a Matéria Legislativa selecionada."
                )

                self.messages.error(err_materia, fail_silently=True)
            return r

    class DeleteView(Crud.DeleteView):

        def form_valid(self, form):
            # LOA-CRUD-064: a exclusão passa pelo delete() do CRUD, que avisa
            # quando a LOA é referenciada por outros registros
            return self.delete(self.request, *self.args, **self.kwargs)

    class UpdateView(Crud.UpdateView):
        form_class = LoaForm

        def get_initial(self):
            initial = super().get_initial()
            if self.object.materia:
                initial["tipo_materia"] = self.object.materia.tipo.id
                initial["numero_materia"] = self.object.materia.numero
                initial["ano_materia"] = self.object.materia.ano
            return initial

        def form_invalid(self, form):
            r = Crud.UpdateView.form_invalid(self, form)

            err_materia = form.errors.get("materia", None)
            if err_materia:
                err_materia = (
                    "Já existe Loa vinculada a Matéria Legislativa selecionada."
                )

                self.messages.error(err_materia, fail_silently=True)
            return r

    class DetailView(Crud.DetailView):
        layout_key = "LoaDetail"

        @property
        def extras_list_url(self):
            btns = []
            u = self.request.user
            if not self.object.materia or not self.object.materia.normajuridica():
                if EmendaLoaService.pode_criar(u):
                    btns.extend(
                        [
                            (
                                reverse(
                                    "cmj.loa:emendaloa_create",
                                    kwargs={"pk": self.kwargs["pk"]},
                                ),
                                "btn-primary",
                                _("Adicionar Emendas Impositivas"),
                            )
                        ]
                    )

            btns = list(filter(None, btns))
            return btns

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} loa-detail"

            return context

        def get(self, request, *args, **kwargs):

            self.object = self.get_object()

            # LOA-CRUD-033: o detalhe segue a visibilidade da lista de LOAs
            if not VisibilidadeLoaService().loa_visivel(request.user, self.object):
                raise Http404

            if self.object.ano <= 2022:
                self.layout_key = "LoaDetailATE2022"

            return super().get(request, *args, **kwargs)

        def hook_materia_ou_norma(self, l, verbose_name="", field_display=""):
            if l.materia:
                nj = l.materia.normajuridica()
                if not nj:
                    get_column = self.get_column("materia|fk_urlize_for_detail", "")
                    return (
                        get_column["verbose_name"],
                        f"""{get_column["text"]}<em class="text-orange"><strong>Processo Legislativo em Andamento</strong></em>""",
                    )

                return (
                    "Norma Jurídica",
                    f"""
                    <a href="{reverse_lazy(
                    'sapl.norma:normajuridica_detail',
                    kwargs={'pk': nj.id})}">{nj}</a>
                """,
                )

            return verbose_name, field_display

        def hook_materia(self, l, verbose_name="", field_display=""):
            if l.materia:
                strm = str(l.materia)
                field_display = field_display.replace(strm, l.materia.epigrafe_short)
            return verbose_name, field_display

        def hook_receita_corrente_liquida(self, l, verbose_name="", field_display=""):

            em_fase_execucao = l.rcl_previa != l.receita_corrente_liquida
            header = f"RCL de {l.ano - (1 if em_fase_execucao else 2)}"
            valor = formats.number_format(
                l.receita_corrente_liquida if em_fase_execucao else l.rcl_previa,
                force_grouping=True,
            )
            return (
                "Receita Corrente Líquida",
                f"""
                {valor}
                <hr>
                <small class="text-gray">
                    <em>{header}</em>
                    <em>(RCL referente ao ano anterior { "à Execução" if em_fase_execucao else "ao Projeto" })</em>
                </small>
            """,
            )

        def _hook_disp_generic(
            self, l, verbose_name="", field_display="", field_type=""
        ):
            """
            Generic function to handle display of disp_* fields

            Parameters:
            - l: Loa object
            - verbose_name: Field verbose name
            - field_display: Field display value
            - field_type: One of 'total', 'saude', or 'diversos'
            - show_per_parliamentarian: Whether to show value per parliamentarian
            """
            percentage_attr = f"perc_disp_{field_type}"
            percentage = getattr(l, percentage_attr, 0)

            result = f"{field_display} <em>({percentage:3.1f}%)</em>"

            # LOA-CRUD-039: divide pelos parlamentares originais (LOA-CRUD-069)
            count_lps = l.loaparlamentar_set.filter(
                parlamentar_id__in=Loa.service.parlamentares_originais(l)
            ).count()

            if count_lps > 0:
                disp_value = getattr(l, f"disp_{field_type}")
                valor_por_parlamentar = formats.number_format(
                    quantize(disp_value / count_lps, rounding=ROUND_DOWN),
                    force_grouping=True,
                )

                result = f"""
                    {field_display}
                    <em>({percentage:3.1f}%)</em>
                    <small><small class="text-gray"><hr><em>Valor por Parlamentar</em>
                        <strong>R$ {valor_por_parlamentar}</strong>
                    </small></small>
                """

            return verbose_name, result

        def hook_disp_total(self, l, verbose_name="", field_display=""):
            return self._hook_disp_generic(l, verbose_name, field_display, "total")

        def hook_disp_saude(self, l, verbose_name="", field_display=""):
            return self._hook_disp_generic(l, verbose_name, field_display, "saude")

        def hook_disp_diversos(self, l, verbose_name="", field_display=""):
            return self._hook_disp_generic(l, verbose_name, field_display, "diversos")

        def hook_resumo_emendas_impositivas(self, *args, **kwargs):
            l = args[0]

            # LOA-CRUD-071: o cálculo fica no serviço; aqui, só o que depende
            # de quem consulta
            resumo = Loa.service.resumo_parlamentares(l)
            totais = resumo["totais"]

            t10 = EmendaLoa.SAUDE
            t99 = EmendaLoa.DIVERSOS

            is_us = self.request.user.is_superuser

            # dsjd display_saude_ja_destinado
            dsjd = 1 if totais[t10]["ja_destinado"] or is_us else 0
            dsit = 1 if totais[t10]["impedimento_tecnico"] or is_us else 0
            dssd = 1 if totais[t10]["sem_destinacao"] or is_us else 0

            # ddjd display_diversos_ja_destinado
            ddjd = 1 if totais[t99]["ja_destinado"] or is_us else 0
            ddit = 1 if totais[t99]["impedimento_tecnico"] or is_us else 0
            ddsd = 1 if totais[t99]["sem_destinacao"] or is_us else 0

            if resumo["existe_pcl"]:
                # Se existir prestação de contas, não exibe colunas de sem destinação.
                ddsd = 0
                dssd = 0

            context = dict(
                resumo_emendas_impositivas=resumo["linhas"],
                tem_norma=resumo["tem_norma"],
                columns=dict(
                    saude=dict(
                        num_columns=dsjd + dsit + dssd,
                        ja_destinado="Valores<br>Já Destinados" if dsjd else "",
                        impedimento_tecnico="Impedimentos<br>Técnicos" if dsit else "",
                        sem_destinacao="Sem<br>Destinação" if dssd else "",
                        totais=totais[t10],
                    ),
                    diversos=dict(
                        num_columns=ddjd + ddit + ddsd,
                        ja_destinado="Valores<br>Já Destinados" if ddjd else "",
                        impedimento_tecnico="Impedimentos<br>Técnicos" if ddit else "",
                        sem_destinacao="Sem<br>Destinação" if ddsd else "",
                        totais=totais[t99],
                    ),
                ),
            )

            template = loader.get_template("loa/widget_loaparlamentar_set_list.html")
            rendered = template.render(context, self.request)
            return "Resumo Geral das Emendas Impositivas Parlamentares", rendered

        def hook_resumo_unidades(self, *args, **kwargs):
            l = args[0]

            resumo = Loa.service.resumo_unidades(l)
            context = dict(
                unidades=resumo["unidades"].items(),
                soma_geral=resumo["soma_geral"],
                tem_norma=Loa.service.tem_norma(l),
                loa=l,
            )

            template = loader.get_template("loa/emendaloa_totalize_unidade.html")
            rendered = template.render(context, self.request)

            return (
                "Resumo Por Unidades Orçamentárias <small>(Totalização na aprovação, sem ajustes por impedimento técnico)</small>",
                rendered,
            )

        def hook_resumo_entidades(self, *args, **kwargs):
            l = args[0]

            resumo = Loa.service.resumo_entidades(l)
            context = dict(
                entidades=resumo["entidades"].items(),
                soma_geral=resumo["soma_geral"],
                tem_norma=Loa.service.tem_norma(l),
                loa=l,
            )

            template = loader.get_template("loa/emendaloa_totalize_entidade.html")
            rendered = template.render(context, self.request)

            return (
                "Resumo Por Entidades <small>(Totalização na aprovação, sem ajustes por impedimento técnico)</small>",
                rendered,
            )

    class PrestacaoContaView(InfoFilterMixin, GoogleRecapthaViewMixin, Crud.DetailView):
        model = Loa
        permission_required = ()
        template_name = "loa/prestacaoconta_detail.html"

        recaptcha_trigger_param = "print"
        recaptcha_trigger_value = "True"
        recaptcha_gate_title = _(
            "Gerar Relatório de Prestação de Contas das Emendas Impositivas"
        )
        recaptcha_success_method = "print"

        @property
        def recaptcha_return_url(self):
            """O "Retornar" do gate volta à prestação de contas desta LOA, com os
            filtros que estavam aplicados: a mesma URL, sem o ``print``."""
            query = self.request.GET.copy()
            query.pop(self.recaptcha_trigger_param, None)
            filtros = query.urlencode()
            return self.request.path + (f"?{filtros}" if filtros else "")

        # nomes das situações no texto dos filtros do relatório
        ROTULOS_DE_SITUACAO = {
            "REGISTRADO": "Registrado",
            "IMPEDIMENTO": "Impedimento",
            "EM_EXECUCAO": "Em Execução",
            "FINALIZADO": "Finalizado",
        }

        def dispatch(self, request, *args, **kwargs):
            # a tela, o gate do reCAPTCHA e o relatório conferem a LOA antes
            # de qualquer outra coisa: a que o usuário não vê responde como
            # inexistente, e a que não virou norma leva ao detalhe da LOA
            loa = Loa.objects.filter(pk=self.kwargs["pk"]).first()
            if loa is None or not VisibilidadeLoaService().loa_visivel(
                request.user, loa
            ):
                raise Http404
            if not loa.materia or not loa.materia.normajuridica():
                return redirect("cmj.loa:loa_detail", pk=loa.pk)
            self.loa = self.object = loa
            return super().dispatch(request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} prestacaoconta-detail"
            return context

        def print(self, request, *args, **kwargs):
            """O relatório para impressão: os mesmos filtros e exercícios do
            painel, com os itens que o ``PrestacaoContaService`` seleciona."""
            # import tardio: o pacote das views da API monta os viewsets
            from cmj.api.loa.views.prestacaoconta import FiltrosDaPrestacaoConta

            get = request.GET
            entrada = {
                "situacao": ",".join(get.getlist("situacao")),
                "search": get.get("search", ""),
                "unidade": get.get("unidade", ""),
                "entidade": get.get("entidade", ""),
                "parlamentar": get.get("parlamentares", ""),
                "tipo__in": ",".join(get.getlist("tipo__in")),
                "ajustes": get.get("ajustes", ""),
                "loas": get.get("loas", ""),
            }
            filtros = FiltrosDaPrestacaoConta(
                data={k: v for k, v in entrada.items() if v != ""}
            )
            servico = PrestacaoContaService()
            try:
                filtros.is_valid(raise_exception=True)
                dados = dict(filtros.validated_data)
                dados["tipos"] = dados.pop("tipo__in", [])
                relatorio = servico.relatorio(request.user, self.loa, dados)
            except servico.LoaIndisponivel:
                raise Http404
            except (DRFValidationError, servico.FiltroInvalido) as e:
                erros = getattr(e, "erros", None) or e.detail
                return HttpResponseBadRequest(
                    format_html(
                        "<h1>Filtro inválido</h1><p>{}</p>",
                        "; ".join(
                            f"{campo}: {' '.join(str(m) for m in mensagens)}"
                            for campo, mensagens in erros.items()
                        ),
                    )
                )

            context = {
                "emendaloa_list": relatorio["emendas"],
                "registroajusteloa_list": relatorio["ajustes"],
                # o nome da LOA sai como texto; a marcação é só a quebra de linha
                "loa_title": format_html(
                    "Prestação de Contas das Emendas Impositivas <br>{}", self.loa
                ),
            }

            # O texto dos filtros aplicados vem do formulário do filterset do
            # que entrou no relatório: emendas, ou ajustes quando só eles entram
            data = get.copy()
            if data.get("situacao"):
                # as situações saem com o nome legível, separadas por vírgula
                situacoes = ",".join(data.getlist("situacao")).split(",")
                data["situacao"] = ", ".join(
                    self.ROTULOS_DE_SITUACAO.get(s.strip(), s.strip())
                    for s in situacoes
                    if s.strip()
                )
            so_ajustes = dados.get("ajustes") and not dados["tipos"]
            if so_ajustes:
                filterset_class = RegistroAjusteLoaFilterSet
                if "parlamentares" in data:
                    data["parlamentares_valor"] = ",".join(data.pop("parlamentares"))
            else:
                filterset_class = EmendaLoaFilterSet
            filterset = filterset_class(
                data=data,
                request=request,
                queryset=filterset_class._meta.model.objects.none(),
            )
            infofilter = (
                self.infofilter(data, form=filterset.form, model=filterset._meta.model)
                or ""
            )
            if dados.get("ajustes"):
                infofilter = format_html("{} - Registros de Ajuste Técnico", infofilter)
            if len(relatorio["loas"]) > 1:
                infofilter = format_html(
                    "{}<br><strong>Exercícios:</strong> {}",
                    infofilter,
                    ", ".join(str(loa.ano) for loa in relatorio["loas"]),
                )
            context["infofilter"] = infofilter

            return self.response_class(
                request=self.request,
                template=["loa/prestacaoconta_print.html"],
                context=context,
                using=self.template_engine,
            )
