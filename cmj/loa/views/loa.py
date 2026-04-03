from decimal import ROUND_DOWN, Decimal

from django.db.models import Q
from django.db.models.aggregates import Sum
from django.http.response import Http404
from django.shortcuts import redirect
from django.template import loader
from django.urls.base import reverse, reverse_lazy
from django.utils import formats, timezone
from django.utils.translation import gettext_lazy as _

from cmj.loa.forms.f_loa import LoaForm
from cmj.loa.models import (
    EmendaLoa,
    EmendaLoaParlamentar,
    Loa,
    RegistroAjusteLoaParlamentar,
)
from cmj.loa.views.mixins import LoaContextDataMixin
from cmj.utils import quantize
from sapl.crud.base import RP_DETAIL, RP_LIST, Crud
from sapl.parlamentares.models import Legislatura, Parlamentar


class LoaCrud(Crud):
    model = Loa
    public = [RP_LIST, RP_DETAIL]
    ordered_list = False
    frontend = Loa._meta.app_label

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

        def hook_header_btn_lista_emendas(self):
            return ""

        def hook_btn_lista_emendas(self, *args, **kwargs):
            l = args[0]
            return f" <em>(Emendas à LOA)</em>", f"/loa/{l.pk}/emendaloa"

        def hook_receita_corrente_liquida(self, *args, **kwargs):
            l = args[0]
            if l.ano < 2023:
                return " - ", args[2]

            ano_atual = timezone.now().year

            rcl_previa = formats.number_format(l.rcl_previa, force_grouping=True)

            if l.ano > ano_atual:
                frase = (
                    "Processo Legislativo em adamento"
                    if not l.materia.normajuridica()
                    else "LOA Aprovada"
                )
                return (
                    f"""
                    {rcl_previa}
                    <small class="text-gray">
                        <small>
                            <em class="text-blue"><strong>{frase}</strong></em>
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
            """,
                "",
            )

        # def hook_header_receita_corrente_liquida(self):
        #     return 'Receita Corrente Líquida - RCL (R$)<br><small class="text-gray">RCL Referente ao ano anterior.</small>'

        def hook_ano(self, *args, **kwargs):
            l = args[0]
            return (
                f"""
            <a href="{args[2]}" title="Detalhes do Cadastro do Orçamento Impositivo">LOA {args[1]}</a><br>
            <div class="btn-group" role="group">
                <a class="btn btn-sm btn-outline-primary" href="/loa/{l.id}/emendaloa" title="Listagem de Emendas à LOA"><i class="fas fa-clipboard-list"></i></a>
                <a class="btn btn-sm btn-outline-primary" href="/loa/{l.id}/oficioajusteloa" title="Ofícios de Ajustes"><i class="fas fa-file-signature"></i></a>
                <a class="btn btn-sm btn-outline-primary" href="/loa/{l.id}/prestacaocontaloa" title="Prestação de Contas"><i class="fas fa-hand-holding-usd"></i></a>
            </div>
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

            return btns

            btns.extend(
                [
                    (
                        reverse(
                            "cmj.loa:emendaloa_list", kwargs={"pk": self.kwargs["pk"]}
                        ),
                        "btn-primary",
                        _("Listar Emendas Impositivas"),
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

            pk = int(kwargs["pk"])
            if pk <= 2022:
                self.layout_key = "LoaDetailATE2022"

            response = super().get(request, *args, **kwargs)
            if not self.object.publicado and request.user.is_anonymous:
                raise Http404
            return response

        def hook_materia_ou_norma(self, l, verbose_name="", field_display=""):
            if l.materia:
                nj = l.materia.normajuridica()
                if not nj:
                    get_column = self.get_column("materia|fk_urlize_for_detail", "")
                    return get_column["verbose_name"], get_column["text"]

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

            legislatura_atual = Legislatura.cache_legislatura_atual()
            materia_in_legislatura_atual = True
            loa_in_legislatura_atual = True

            if l.materia:
                materia_in_legislatura_atual = (
                    legislatura_atual["data_inicio"]
                    <= l.materia.data_apresentacao
                    <= legislatura_atual["data_fim"]
                )
                loa_in_legislatura_atual = (
                    legislatura_atual["data_inicio"].year
                    <= l.ano
                    <= legislatura_atual["data_fim"].year
                )

            lps = l.loaparlamentar_set.all()
            count_lps = lps.count()

            if not loa_in_legislatura_atual or not materia_in_legislatura_atual:
                count_lps = Parlamentar.objects.filter(ativo=True).count()

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

            loaparlamentares = l.loaparlamentar_set.order_by(
                "-parlamentar__ativo", "parlamentar__nome_parlamentar"
            )

            resumo_emendas_impositivas = []

            totais = {}

            for lp in loaparlamentares:
                # print(f"Calculando resumo para parlamentar {lp}...")

                resumo_parlamentar = {"loaparlamentar": lp}
                for k, v in EmendaLoa.TIPOEMENDALOA_CHOICE[:2]:
                    resumo_parlamentar[k] = {"name": v}
                    if k not in totais:
                        totais[k] = dict(
                            ja_destinado=Decimal("0.00"),
                            impedimento_tecnico=Decimal("0.00"),
                            sem_destinacao=Decimal("0.00"),
                        )

                    # Inicia com o valor disponível para destinação, que é o valor total menos o que já foi destinado
                    if k == EmendaLoa.SAUDE:
                        resumo_parlamentar[k]["sem_destinacao"] = lp.disp_saude
                    elif k == EmendaLoa.DIVERSOS:
                        resumo_parlamentar[k]["sem_destinacao"] = lp.disp_diversos

                    resumo_parlamentar[k]["impedimento_tecnico"] = 0
                    resumo_parlamentar[k]["ja_destinado"] = 0

                    params = dict(
                        parlamentar=lp.parlamentar,
                        emendaloa__loa=self.object,
                        emendaloa__tipo=k,
                    )

                    # 1 - Soma todas as destinações feitas para o parlamentar na LOA e tipo de emenda
                    # incluindo as que estão em fase de impedimento técnico
                    totdb_ja_destinado = EmendaLoaParlamentar.objects.filter(
                        **params
                    ).aggregate(Sum("valor"))

                    # 2 - Soma o valor de emendas que já estiveram em fase de impedimento técnico, para mostrar o impacto total dos impedimentos técnicos

                    totdb_imp_tecnico = (
                        EmendaLoaParlamentar.objects.filter(**params)
                        .filter(
                            emendaloa__emendaloahistoricofase_set__fase__in=[
                                EmendaLoa.IMPEDIMENTO_TECNICO,
                                EmendaLoa.EMENDA_REDEFINIDA,
                            ]
                        )
                        .order_by("emendaloa")
                        .distinct()
                        .aggregate(Sum("valor"))
                    )

                    # 3 - Soma os ajustes feitos para aquele parlamentar, LOA e tipo de emenda, que podem ser positivos ou negativos
                    totdb_reg_reaj_com_emenda = (
                        RegistroAjusteLoaParlamentar.objects.filter(
                            parlamentar=lp.parlamentar,
                            registro__emendaloa__tipo=k,
                            registro__oficio_ajuste_loa__loa=l,
                            registro__tipo=k,
                            valor__gte=Decimal("0.00"),
                        )
                        .distinct()
                        .aggregate(Sum("valor"))
                    )

                    totdb_reg_reaj_sem_emenda = (
                        RegistroAjusteLoaParlamentar.objects.filter(
                            parlamentar=lp.parlamentar,
                            registro__emendaloa__isnull=True,
                            registro__oficio_ajuste_loa__loa=l,
                            registro__tipo=k,
                            valor__gte=Decimal("0.00"),
                        )
                        .distinct()
                        .aggregate(Sum("valor"))
                    )

                    totdb_ja_destinado = totdb_ja_destinado["valor__sum"] or Decimal(
                        "0.00"
                    )
                    totdb_imp_tecnico = totdb_imp_tecnico["valor__sum"] or Decimal(
                        "0.00"
                    )
                    totdb_reg_reaj_com_emenda = totdb_reg_reaj_com_emenda[
                        "valor__sum"
                    ] or Decimal("0.00")
                    totdb_reg_reaj_sem_emenda = totdb_reg_reaj_sem_emenda[
                        "valor__sum"
                    ] or Decimal("0.00")

                    tot_remanescente = (
                        resumo_parlamentar[k]["sem_destinacao"] - totdb_ja_destinado
                    )

                    # GRANDE FASE 1: Tramitação até a aprovação legislativa
                    resumo_parlamentar[k]["sem_destinacao"] = (
                        resumo_parlamentar[k]["sem_destinacao"] - totdb_ja_destinado
                    )
                    resumo_parlamentar[k]["ja_destinado"] = totdb_ja_destinado

                    # GRANDE FASE 2: Impedimentos Técnicos
                    resumo_parlamentar[k]["impedimento_tecnico"] = totdb_imp_tecnico
                    resumo_parlamentar[k]["ja_destinado"] = (
                        resumo_parlamentar[k]["ja_destinado"]
                        - resumo_parlamentar[k]["impedimento_tecnico"]
                    )
                    resumo_parlamentar[k]["sem_destinacao"] = (
                        resumo_parlamentar[k]["sem_destinacao"]
                        + resumo_parlamentar[k]["impedimento_tecnico"]
                    )

                    # GRANDE FASE 3: Ajustes pós-aprovação legislativa
                    resumo_parlamentar[k]["ja_destinado"] = (
                        resumo_parlamentar[k]["ja_destinado"]
                        + totdb_reg_reaj_com_emenda
                        + totdb_reg_reaj_sem_emenda
                    )
                    resumo_parlamentar[k]["sem_destinacao"] = (
                        resumo_parlamentar[k]["sem_destinacao"]
                        - totdb_reg_reaj_com_emenda
                        - totdb_reg_reaj_sem_emenda
                    )
                    resumo_parlamentar[k]["impedimento_tecnico"] = (
                        resumo_parlamentar[k]["impedimento_tecnico"]
                        - totdb_reg_reaj_com_emenda
                        # + (tot_remanescente - totdb_reg_reaj_sem_emenda)
                    )

                    # EXTRAS:
                    # - Se o parlamentar estiver ativo, o valor que está em fase de impedimento técnico
                    #   é acrescido do remanescente, para mostrar o impacto total no valor disponível
                    #   para destinação.
                    if lp.parlamentar.ativo:
                        resumo_parlamentar[k][
                            "impedimento_tecnico"
                        ] = resumo_parlamentar[k]["impedimento_tecnico"] + (
                            tot_remanescente - totdb_reg_reaj_sem_emenda
                        )

                    if abs(resumo_parlamentar[k]["impedimento_tecnico"]) == abs(
                        tot_remanescente
                    ) and (totdb_reg_reaj_com_emenda or totdb_reg_reaj_sem_emenda):
                        resumo_parlamentar[k]["impedimento_tecnico"] = Decimal("0.00")

                    # TOTALIZAÇÃO - Acumula os totais para exibição no header da tabela
                    totais[k]["ja_destinado"] += resumo_parlamentar[k]["ja_destinado"]
                    totais[k]["impedimento_tecnico"] += resumo_parlamentar[k][
                        "impedimento_tecnico"
                    ]
                    totais[k]["sem_destinacao"] += resumo_parlamentar[k][
                        "sem_destinacao"
                    ]

                resumo_emendas_impositivas.append(resumo_parlamentar)

            resumo_emendas_impositivas.sort(
                key=lambda x: (
                    not x["loaparlamentar"].parlamentar.ativo,
                    # -x[10]['ja_destinado'],
                    x["loaparlamentar"].parlamentar.nome_parlamentar,
                )
            )

            is_us = self.request.user.is_superuser

            t10 = EmendaLoa.SAUDE
            t99 = EmendaLoa.DIVERSOS
            # dsjd display_saude_ja_destinado
            dsjd = 1 if totais[t10]["ja_destinado"] or is_us else 0
            dsit = 1 if totais[t10]["impedimento_tecnico"] or is_us else 0
            dssd = 1 if totais[t10]["sem_destinacao"] or is_us else 0

            # ddjd display_diversos_ja_destinado
            ddjd = 1 if totais[t99]["ja_destinado"] or is_us else 0
            ddit = 1 if totais[t99]["impedimento_tecnico"] or is_us else 0
            ddsd = 1 if totais[t99]["sem_destinacao"] or is_us else 0

            context = dict(
                resumo_emendas_impositivas=resumo_emendas_impositivas,
                columns=dict(
                    saude=dict(
                        num_columns=dsjd + dsit + dssd,
                        ja_destinado="Valores<br>Já Destinados" if dsjd else "",
                        impedimento_tecnico="Impedimentos<br>Técnicos" if dsit else "",
                        sem_destinacao=(
                            (
                                "Sem Destinação"
                                if not l.materia
                                or l.materia
                                and not l.materia.normajuridica()
                                else "Remanescente"
                            )
                            if dssd
                            else ""
                        ),
                    ),
                    diversos=dict(
                        num_columns=ddjd + ddit + ddsd,
                        ja_destinado="Valores<br>Já Destinados" if ddjd else "",
                        impedimento_tecnico="Impedimentos<br>Técnicos" if ddit else "",
                        sem_destinacao=(
                            (
                                "Sem Destinação"
                                if not l.materia
                                or l.materia
                                and not l.materia.normajuridica()
                                else "Remanescente"
                            )
                            if ddsd
                            else ""
                        ),
                    ),
                ),
            )

            # TODO: para o detail da LOA, parlamentar ativo e inativo deve ser mostrado
            # sobre o contexto da legislatura vigente no ano de execução da LOA,
            # e não pelo status no cadastro Parlamentar.
            template = loader.get_template("loa/widget_loaparlamentar_set_list.html")
            rendered = template.render(context, self.request)
            return "Resumo Geral das Emendas Impositivas Parlamentares", rendered

        def hook_resumo_unidades(self, *args, **kwargs):
            l = args[0]

            soma_geral = Decimal("0.00")
            unidades = {}
            for el in (
                EmendaLoa.objects.filter(loa=l, tipo__gt=0)
                .values(
                    "unidade__especificacao",
                    "emendaloaparlamentar_set__parlamentar__id",
                    "emendaloaparlamentar_set__parlamentar__nome_parlamentar",
                )
                .order_by(
                    "unidade__especificacao",
                    "emendaloaparlamentar_set__parlamentar__nome_parlamentar",
                )
                .annotate(
                    valor_parte_parlamentar=Sum("emendaloaparlamentar_set__valor")
                )
            ):
                if el["unidade__especificacao"] not in unidades:
                    unidades[el["unidade__especificacao"]] = {
                        "parlamentares": [],
                        "soma_unidade": Decimal("0.00"),
                    }

                unidades[el["unidade__especificacao"]]["soma_unidade"] += el[
                    "valor_parte_parlamentar"
                ]

                unidades[el["unidade__especificacao"]]["parlamentares"].append(
                    {
                        "id": el["emendaloaparlamentar_set__parlamentar__id"],
                        "nome_parlamentar": el[
                            "emendaloaparlamentar_set__parlamentar__nome_parlamentar"
                        ],
                        "soma_valor": el["valor_parte_parlamentar"],
                    }
                )

                soma_geral += el["valor_parte_parlamentar"]

            context = dict(unidades=unidades.items(), soma_geral=soma_geral, loa=l)

            template = loader.get_template("loa/emendaloa_totalize_unidade.html")
            rendered = template.render(context, self.request)

            return (
                "Resumo Por Unidades Orçamentárias <small>(Totalização na aprovação, sem ajustes por impedimento técnico)</small>",
                rendered,
            )

        def hook_resumo_entidades(self, *args, **kwargs):
            l = args[0]

            soma_geral = Decimal("0.00")
            entidades = {}
            for el in (
                EmendaLoa.objects.filter(loa=l, tipo__gt=0)
                .values(
                    "tipo",
                    "entidade__nome_fantasia",
                    "unidade__especificacao",
                    "emendaloaparlamentar_set__parlamentar__id",
                    "emendaloaparlamentar_set__parlamentar__nome_parlamentar",
                )
                .order_by(
                    "tipo",
                    "entidade__nome_fantasia",
                    "emendaloaparlamentar_set__parlamentar__nome_parlamentar",
                )
                .annotate(
                    valor_parte_parlamentar=Sum("emendaloaparlamentar_set__valor")
                )
            ):
                nom_entidade = el["entidade__nome_fantasia"]
                if not nom_entidade:
                    continue

                el["entidade__nome_fantasia"] = nom_entidade.upper()
                if el["entidade__nome_fantasia"] not in entidades:
                    entidades[el["entidade__nome_fantasia"]] = {
                        "tipo": el["tipo"],
                        "parlamentares": [],
                        "soma_entidade": Decimal("0.00"),
                    }

                entidades[el["entidade__nome_fantasia"]]["soma_entidade"] += el[
                    "valor_parte_parlamentar"
                ]
                entidades[el["entidade__nome_fantasia"]]["parlamentares"].append(
                    {
                        "id": el["emendaloaparlamentar_set__parlamentar__id"],
                        "nome_parlamentar": el[
                            "emendaloaparlamentar_set__parlamentar__nome_parlamentar"
                        ],
                        "soma_valor": el["valor_parte_parlamentar"],
                    }
                )

                soma_geral += el["valor_parte_parlamentar"]

            context = dict(entidades=entidades.items(), soma_geral=soma_geral, loa=l)

            template = loader.get_template("loa/emendaloa_totalize_entidade.html")
            rendered = template.render(context, self.request)

            return (
                "Resumo Por Entidades <small>(Totalização na aprovação, sem ajustes por impedimento técnico)</small>",
                rendered,
            )
