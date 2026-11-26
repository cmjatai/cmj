import logging
import re
import tempfile
import zipfile
from _collections import OrderedDict
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Exists, OuterRef, Q
from django.db.models.aggregates import Sum
from django.http import Http404
from django.http.response import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.template import loader
from django.template.loader import render_to_string
from django.urls.base import reverse, reverse_lazy
from django.utils import formats
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from cmj.core.models import AuditLog
from cmj.loa import tasks
from cmj.loa.forms.f_emendaloa import EmendaLoaFilterSet, EmendaLoaForm
from cmj.loa.models import (
    Despesa,
    EmendaLoa,
    EmendaLoaParlamentar,
    EmendaLoaRegistroContabil,
    Loa,
    RegistroAjusteLoa,
)
from cmj.loa.views.v_mixins import LoaContextDataMixin
from cmj.mixins import GoogleRecapthaViewMixin
from cmj.utils import TimeExecution
from cmj.utils.utils_report import make_pdf, pdf_base_url
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud
from sapl.parlamentares.models import Parlamentar

logger = logging.getLogger(__name__)


def alinhar_valor(texto, largura):
    """Alinha "R$ <valor>" à largura, com espaços depois do primeiro espaço
    (LOA-LST-060); sem espaço, alinha o texto inteiro à direita."""
    if " " not in texto:
        return texto.rjust(largura)
    cabeca, resto = texto.split(" ", 1)
    return f"{cabeca} {resto.rjust(largura - len(cabeca) - 1)}"


ARQUIVO_NAO_INCLUIDAS = "LEIA-ME_emendas_nao_incluidas.txt"


def texto_emendas_nao_incluidas(emendas):
    linhas = [
        "Não foi possível gerar o PDF das emendas abaixo, que ficaram fora deste "
        "arquivo. Tente baixar novamente; se o problema continuar, procure o "
        "suporte informando os números abaixo.",
        "",
    ]
    for emenda in emendas:
        materia = emenda.materia.epigrafe_short if emenda.materia else "sem matéria"
        linhas.append(f"- Emenda {emenda.id} ({materia})")
    return "\n".join(linhas) + "\n"


# Rótulo da dimensão vazia no título do grupo do PDF ("Sem ...", LOA-LST-057)
ROTULO_SEM_DIMENSAO = {
    "despesa__orgao": "órgão",
    "despesa__unidade": "unidade orçamentária",
    "despesa__funcao": "função",
    "despesa__subfuncao": "subfunção",
    "despesa__programa": "programa",
    "despesa__acao": "ação",
    "despesa__natureza": "natureza da despesa",
    "despesa__fonte": "fonte de recursos",
    "entidade": "entidade",
}


class EmendaLoaCrud(MasterDetailCrud):
    model = EmendaLoa
    parent_field = "loa"
    public = [RP_LIST, RP_DETAIL]
    frontend = EmendaLoa._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        list_field_names = [("id",)]

        @property
        def ordered_list(self):
            return False

        @property
        def create_url(self):
            url = super().create_url
            if (
                not url
                and not self.request.user.is_anonymous
                and (
                    self.request.user.operadorautor_set.exists()
                    or self.request.user.is_superuser
                )
            ):
                url = self.resolve_url("create", args=(self.kwargs["pk"],))
            return url

        @property
        def update_url(self):

            url = super().update_url
            if url or self.request.user.is_anonymous:
                return url

            if not url and self.object.fase >= EmendaLoa.EM_TRAMITACAO:
                return ""

            url_perm = self.resolve_url("update", args=(self.object.id,))

            if (
                self.request.user.has_perm("loa.emendaloa_full_editor")
                and EmendaLoa.PROPOSTA < self.object.fase < EmendaLoa.EM_TRAMITACAO
            ):
                return url_perm

            # LOA-EMD-076: só o autor do dono; coautores só consultam
            if EmendaLoa.service.e_autor_da_emenda(self.request.user, self.object):
                return url_perm
            return url_perm if self.request.user == self.object.owner else ""

        @property
        def detail_url(self):

            url = super().update_url
            if url or self.request.user.is_anonymous:
                return url

            if (
                self.request.user.has_perm("loa.emendaloa_full_editor")
                or self.request.user.operadorautor_set.exists()
            ):
                url = self.resolve_url("detail", args=(self.object.id,))

            return url

        @property
        def layout_display(self):
            l = super().layout_display

            if not self.object.materia:
                l.pop()

            return l

    class ListView(GoogleRecapthaViewMixin, FilterView, MasterDetailCrud.ListView):
        filterset_class = EmendaLoaFilterSet
        # LOA-LST-025: filtro inválido é ignorado e o campo mostra o erro
        strict = False

        # LOA-LST-085: anônimo passa pelo reCAPTCHA antes de gerar o PDF
        recaptcha_trigger_param = "pdf"
        recaptcha_gate_title = _("Gerar Listagem das Emendas em PDF")
        recaptcha_gate_button = _("Gerar PDF")
        recaptcha_success_method = "pdf_apos_recaptcha"

        def _is_recaptcha_triggered(self, request):
            return request.user.is_anonymous and super()._is_recaptcha_triggered(
                request
            )

        @property
        def recaptcha_return_url(self):
            return self.request.path

        def pdf_apos_recaptcha(self, request, *args, **kwargs):
            # Os filtros seguem na query string do POST do gate
            return self.get(request, *args, **kwargs)

        @cached_property
        def tem_emendas_liberadas(self):
            """LOA-LST-015: operador com emenda liberada do seu autor na LOA."""
            if (
                self.request.user.is_anonymous
                or not self.request.user.operadorautor_set.exists()
            ):
                return False

            return (
                self.get_emendas_criadas_por_operador_mesmo_autor()
                .filter(fase__gte=EmendaLoa.LIBERACAO_CONTABIL)
                .exists()
            )

        @property
        def extras_url(self):
            # LOA-LST-015: o registro é um formulário POST no template
            # (LOA-LST-016), não um link
            if not self.tem_emendas_liberadas:
                return []

            return [
                (
                    reverse_lazy(
                        "cmj.loa:emendaloa_list", kwargs={"pk": self.kwargs["pk"]}
                    )
                    + "?zip",
                    "btn-success",
                    """<span title="Baixar Emendas Impositivas/Modificativas em arquivo ZIP">
                        <i class="far fa-file-archive"></i> Baixar Emendas Liberadas</span>
                    """,
                ),
            ]

        def get_emendas_criadas_por_operador_mesmo_autor(self):
            if self.request.user.is_anonymous:
                return self.get_queryset().none()
            # LOA-LST-015: o operador opera um único autor; botões, ZIP e
            # registro consideram as emendas dos operadores desse autor
            operador = self.request.user.operadorautor_set.first()
            if not operador:
                return self.get_queryset().none()
            OperadorAutor = type(operador)

            return self.get_queryset().filter(
                loa=self.loa,
                owner__id__in=OperadorAutor.objects.filter(
                    autor=operador.autor_id
                ).values_list("user", flat=True),
            )

        @property
        def title(self):
            return f"""Emendas Impositivas/Modificativas à LOA {self.loa.ano} <small>({self.loa.materia.epigrafe_short if self.loa.materia else ''})</small>
                """

        def dispatch(self, request, *args, **kwargs):
            # LOA-LST-003: LOA inexistente ou que o usuário não pode ver responde
            # 404, antes até da verificação reCAPTCHA do PDF
            self.loa = get_object_or_404(
                EmendaLoa.service.loas_visiveis(request.user), pk=kwargs["pk"]
            )
            # LOA-LST-087: sem matéria não há emenda a listar
            if not self.loa.materia_id:
                raise Http404("A LOA ainda não tem matéria legislativa vinculada.")
            return super().dispatch(request, *args, **kwargs)

        def get(self, request, *args, **kwargs):
            # LOA-LST-016: o registro altera dados e só é aceito por POST
            if "registrar" in self.request.GET:
                return HttpResponseNotAllowed(["POST"])
            return FilterView.get(self, request, *args, **kwargs)

        def post(self, request, *args, **kwargs):
            # LOA-LST-016: único uso do POST nesta tela (o do reCAPTCHA do PDF é
            # tratado antes, no dispatch do mixin); o CSRF é exigido pelo
            # middleware
            if "registrar" not in request.POST:
                return HttpResponseNotAllowed(["GET"])
            # LOA-LST-017: a recusa volta para a listagem com o aviso; o
            # registro iniciado vai para a lista de proposições
            recusa = self.registrar_emendas_liberadas(request)
            if recusa:
                return recusa
            return redirect(reverse_lazy("sapl.materia:proposicao_list"))

        def registrar_emendas_liberadas(self, request, *args, **kwargs):

            from sapl.base.models import OperadorAutor

            # verifica se existe emenda desse usuario que está com metadata setado para register

            if request.user.is_anonymous:
                messages.warning(
                    self.request, "Ação não permitida para usuários anônimos."
                )
                return redirect(
                    reverse_lazy("cmj.loa:emendaloa_list", kwargs={"pk": self.loa.id})
                )

            user_id = request.user.id

            autor_operado = OperadorAutor.objects.filter(user_id=user_id).first()
            if not autor_operado:
                messages.warning(
                    self.request,
                    "Ação não permitida. Usuário não é operador de nenhum autor parlamentar.",
                )

                return redirect(
                    reverse_lazy("cmj.loa:emendaloa_list", kwargs={"pk": self.loa.id})
                )

            autor_operado = autor_operado.autor
            operadores = OperadorAutor.objects.filter(autor=autor_operado).values_list(
                "user_id", flat=True
            )

            emendas_sendo_registradas = EmendaLoa.objects.filter(
                loa=self.loa,
                owner__id__in=operadores,
                fase__gte=EmendaLoa.LIBERACAO_CONTABIL,
                metadata__register_emendaloa_proposicao_task__isnull=False,
            )

            if emendas_sendo_registradas.exists():
                messages.warning(
                    self.request,
                    "Ação não permitida. Existem emendas liberadas que estão sendo registradas no módulo de proposições. Aguarde o término do processo antes de iniciar um novo.",
                )

                return redirect(reverse_lazy("sapl.materia:proposicao_list"))

            messages.info(
                self.request,
                "Iniciando o registro aqui no módulo de proposições das emendas liberadas... atualize esta página para acompanhar o progresso.",
            )
            params_task = (self.loa.id, self.request.user.id)
            if not settings.DEBUG or (
                settings.DEBUG
                and settings.FOLDER_DEBUG_CONTAINER == settings.PROJECT_DIR
            ):
                tasks.task_register_emendaloa_proposicao.apply_async(
                    params_task, countdown=0
                )
            else:
                tasks.task_register_emendaloa_proposicao_function(*params_task)

        def render_to_response(self, context, **response_kwargs):
            if "pdf" in self.request.GET:
                # LOA-LST-025: com filtro inválido o PDF não é gerado; a tela
                # mostra os filtros com o aviso no campo
                if self.filterset.is_bound and not self.filterset.is_valid():
                    messages.warning(
                        self.request,
                        "Há filtros inválidos, indicados no formulário. "
                        "Corrija-os para gerar o PDF.",
                    )
                    return super().render_to_response(context, **response_kwargs)
                return self.makepdf(context, **response_kwargs)
            elif "zip" in self.request.GET:
                return self.makezip(context, **response_kwargs)
            return super().render_to_response(context, **response_kwargs)

        def makezip(self, context, **response_kwargs):
            user = self.request.user
            if user.is_anonymous:
                raise PermissionDenied()

            if not user.is_superuser and not user.operadorautor_set.exists():
                raise PermissionDenied()

            # LOA-LST-019: o PDF é gerado no processo; a base dos endereços
            # relativos vem da configuração, não do Host da requisição
            base_url = settings.BASE_URL

            emendas = self.get_emendas_criadas_por_operador_mesmo_autor().filter(
                fase__gte=EmendaLoa.LIBERACAO_CONTABIL
            )

            if not emendas.exists():
                messages.info(
                    self.request,
                    "Nenhuma Emenda Impositiva/Modificativa disponível para download.",
                )
                return super().render_to_response(context, **response_kwargs)

            autoroperado_id = user.operadorautor_set.values_list(
                "autor", flat=True
            ).first()

            with tempfile.SpooledTemporaryFile(max_size=512000000) as tmp:
                with zipfile.ZipFile(tmp, "w") as file:

                    nao_incluidas = []
                    for emenda in emendas:
                        try:
                            pdf = EmendaLoa.service.documento_pdf(emenda, base_url)
                        except Exception:
                            logger.exception(
                                f"Erro ao gerar o PDF da emenda {emenda.id} para o ZIP."
                            )
                            pdf = None
                            nao_incluidas.append(emenda)

                        prefixo = (
                            "coletiva"
                            if emenda.emendaloaparlamentar_set.count() > 1
                            else "individual"
                        )

                        if pdf:
                            nome_emenda = f"{prefixo}_{emenda.id}_sem_vinculo_com_proposicao_{emenda.loa.ano}"
                            if emenda.materia:
                                nome_emenda = f"{prefixo}_{emenda.id}_ja_procolocada_{emenda.materia.tipo.sigla}_{emenda.materia.numero}_{emenda.materia.ano}"
                            elif emenda.proposicao:
                                nome_emenda = f"{prefixo}_{emenda.id}_com_proposicao_gerada_{emenda.proposicao.tipo.descricao}_{emenda.proposicao.numero_proposicao}_{emenda.proposicao.ano}"
                            nome_emenda = slugify(nome_emenda)

                            file.writestr(f"{nome_emenda}.pdf", pdf)

                    # LOA-LST-019: a emenda omitida por falha no PDF é listada
                    # num arquivo do próprio ZIP
                    if nao_incluidas:
                        file.writestr(
                            ARQUIVO_NAO_INCLUIDAS,
                            texto_emendas_nao_incluidas(nao_incluidas),
                        )
                tmp.seek(0)
                response = HttpResponse(tmp.read(), content_type="application/zip")
                response["Content-Disposition"] = (
                    f'attachment; filename="emendaloa_{self.loa.ano}_autor_{autoroperado_id}.zip"'
                )
                response["Cache-Control"] = "no-cache"
                response["Pragma"] = "no-cache"
                response["Expires"] = 0
                return response

        def makepdf(self, context, **response_kwargs):
            self.paginate_by = 0
            base_url = pdf_base_url(self.request)  # LOA-LST-086
            # LOA-LST-046: erro na geração vai para o log com a causa, e o
            # usuário volta para a tela com os filtros e um aviso
            try:
                with TimeExecution(
                    print_date=settings.DEBUG, label="Make Context PDF EmendaLoa List"
                ):
                    context_pdf = self.get_context_data_makepdf()

                with TimeExecution(
                    print_date=settings.DEBUG, label="Render Html EmendaLoa List"
                ):
                    template = render_to_string(
                        "loa/pdf/emendaloa_list.html", context_pdf
                    )

                with TimeExecution(
                    print_date=settings.DEBUG, label="Generate PDF EmendaLoa List"
                ):
                    pdf_file = make_pdf(base_url=base_url, main_template=template)
            except Exception:
                logger.exception(
                    f"Erro ao gerar o PDF da listagem de emendas da LOA {self.loa.id} "
                    f"com os parâmetros: {self.request.GET.urlencode()}"
                )
                messages.error(
                    self.request,
                    "Não foi possível gerar o PDF com esses filtros e totalizações.",
                )
                return super().render_to_response(context, **response_kwargs)

            response = HttpResponse(pdf_file, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'inline; filename="emendaloa_{self.loa.ano}.pdf"'
            )
            response["Cache-Control"] = "no-cache"
            response["Pragma"] = "no-cache"
            response["Expires"] = 0
            return response

        def get_context_data_makepdf(self):

            cd = self.filterset.form.cleaned_data

            title = "Listagem Geral das Emendas <small>{}</small>"

            filters = []
            if cd.get("parlamentares", ""):
                filtro = f'<strong>Parlamentares:</strong> {" / ".join(map(lambda x: escape(str(x)), cd["parlamentares"]))}'
                filters.append(filtro)

            if cd.get("finalidade", ""):
                filtro = f'<strong>Finalidade:</strong> {escape(cd["finalidade"])}'
                filters.append(filtro)

            if cd.get("tipo", ""):
                dt = dict(
                    map(lambda x: (str(x[0]), x[1]), EmendaLoa.TIPOEMENDALOA_CHOICE)
                )
                filtro = f'<strong>Tipos de Emenda:</strong> {" / ".join(map(lambda x: escape(str(dt[x])), cd["tipo"]))}'
                filters.append(filtro)

            if cd.get("fase", ""):
                dt = dict(map(lambda x: (str(x[0]), x[1]), EmendaLoa.FASE_CHOICE))
                filtro = f'<strong>Fases de Emenda:</strong> {" / ".join(map(lambda x: escape(str(dt[x])), cd["fase"]))}'
                filters.append(filtro)

            # LOA-LST-047: todo filtro que muda o conteúdo aparece no PDF
            if cd.get("entidade"):
                filtro = (
                    f"<strong>Entidade:</strong> {escape(cd['entidade'].nome_fantasia)}"
                )
                filters.append(filtro)

            if cd.get("unidade"):
                filtro = (
                    f"<strong>Unidade Orçamentária:</strong> {escape(cd['unidade'])}"
                )
                filters.append(filtro)

            if cd.get("autoria") in ("individual", "coletiva"):
                autoria = dict(self.filterset.filters["autoria"].extra["choices"])
                filtro = f"<strong>Autoria:</strong> {escape(autoria[cd['autoria']])}"
                filters.append(filtro)

            if cd.get("indicacao"):
                filtro = f"<strong>Indicação:</strong> {escape(cd['indicacao'])}"
                filters.append(filtro)

            if filters:
                filters.insert(0, "<strong>FILTROS APLICADOS</strong>")

            context = {
                "object": self.loa,
                "loa": self.loa,
                "tipo_agrupamento": cd.get("tipo_agrupamento", ""),
                "title": title,
                "filters": "<br>".join(filters),
                "groups": [],
                "quebrar_pagina": cd.get("quebrar_pagina", False),
            }

            def render_col_emenda(item):

                materia = ""
                if item.materia:
                    materia = f"""
                            <span class="materia">
                                <a href="{reverse('cmj.loa:emendaloa_detail',kwargs={'pk': item.id})}">
                                {escape(item.materia.epigrafe_short)}
                                </a>
                            </span>
                    """
                else:
                    materia = f"""
                            <span class="materia">
                                <a href="{reverse('cmj.loa:emendaloa_detail',kwargs={'pk': item.id})}">
                                Emenda em Elaboração
                                </a>
                            </span>
                    """

                autores = f"""
                    <small>
                        <strong>Autoria:</strong> {' - '.join(map(lambda x: escape(str(x)), item.parlamentares.all()))}
                    </small>
                """

                # LOA-LST-089: a emenda cujo valor final é zero (LOA-FASE-061 e
                # LOA-FASE-044) é sinalizada; o PDF mostra o valor original
                aviso = ""
                if item.pdf_tem_ajuste:
                    aviso = "Possui ajuste técnico, não contemplado neste relatório."
                elif item.fase == EmendaLoa.IMPEDIMENTO_TECNICO:
                    aviso = "Em impedimento técnico."
                if aviso:
                    aviso = f'<small class="aviso-ajuste">{aviso}</small>'

                col_emenda = f"""
                    <div class="loa-mat">
                        {materia}
                        - <small class="tipo">{escape(item.get_tipo_display())}</small>
                        - {autores}
                        {aviso}
                        <span class="indicacao">{escape(item.indicacao)}</span>
                        <div>
                            {escape(item.finalidade_format)}
                        </div>
                        <ul></ul>
                    </div>
                """
                return col_emenda

            total = Decimal("0.00")
            self.object_list = self.object_list.order_by("materia__numero").annotate(
                pdf_tem_ajuste=Exists(
                    RegistroAjusteLoa.objects.filter(emendaloa=OuterRef("pk"))
                )
            )
            if not cd.get("agrupamento", []):
                # LOA-LST-080: o marcador do título é limpo antes do retorno do
                # resultado vazio
                context["title"] = context["title"].replace("{}", "")

                if not self.object_list.exists():
                    return context

                sub_total = self.object_list.aggregate(Sum("valor"))

                total += sub_total["valor__sum"]

                columns = ["Emendas", "Valores"]

                # if not cd['tipo'] or len(cd['tipo']) > 1:
                #    columns.insert(1, 'Tipos')

                rows = []

                for item in self.object_list:
                    cols = []
                    col_emenda = render_col_emenda(item)
                    cols.append((col_emenda, ""))

                    # if not cd['tipo'] or len(cd['tipo']) > 1:
                    #    cols.append((item.get_tipo_display(), 'text-center'))

                    cols.append((item.str_valor, "text-right"))

                    rows.append(cols)

                group = {
                    "title": "",
                    "columns": columns,
                    "ncols_menos2": len(columns) - 2,
                    "ncols_menos1": len(columns) - 1,
                    "rows": rows,
                    "sub_total_emendas": formats.number_format(
                        sub_total["valor__sum"], force_grouping=True
                    ),
                    "agrupamento": False,
                }
                context["groups"].append(group)

            else:
                agrupamento1 = list(
                    map(
                        lambda x: f"{x}__codigo" if x != "entidade" else x,
                        cd["agrupamento"],
                    )
                )
                agrupamento2 = list(
                    map(
                        lambda x: f"{x}__especificacao" if x != "entidade" else x,
                        cd["agrupamento"],
                    )
                )
                agrupamento = []
                for i in range(len(agrupamento1)):
                    agrupamento.append(agrupamento1[i])
                    agrupamento.append(agrupamento2[i])

                # agrupamento terá itens strings como:
                # ['despesa__programa__codigo', 'despesa__unidade__codigo']
                # desmembre todos de modo que resulte: 'despesa', 'despesa__programa', 'despesa__programa__codigo'
                agrup = set()
                for ag in agrupamento:
                    parts = ag.split("__")
                    for i in range(1, len(parts) + 1):
                        sub_ag = "__".join(parts[:i])
                        if sub_ag not in agrup:
                            agrup.add(sub_ag)
                agrup = list(agrup)

                emendas_filtradas_ids = self.object_list.values_list("id", flat=True)
                emendas_dict = {e.id: e for e in self.object_list}

                via = ""
                if cd["tipo_agrupamento"] == "insercao":
                    via = "<br>* Agrupado  - Via dotações de inserção."
                elif cd["tipo_agrupamento"] == "deducao":
                    via = "<br>* Agrupado  - Via dotações de dedução."
                else:
                    via = "<br>* Agrupado  - Via Entidades / Unidade Orçamentária."

                context["title"] = context["title"].format(f"{via}")

                groups = OrderedDict()

                if cd["tipo_agrupamento"] != "sem_registro":
                    dimensoes = list(cd["agrupamento"])
                    lookup_totalizador = (
                        "gt" if cd["tipo_agrupamento"] == "insercao" else "lt"
                    )

                    agrup.extend(["emendaloa", "valor"])
                    registros_contabeis = (
                        EmendaLoaRegistroContabil.objects.filter(
                            emendaloa__in=emendas_filtradas_ids,
                            **{f"valor__{lookup_totalizador}": Decimal("0.00")},
                        )
                        .order_by(*agrupamento, "emendaloa")
                        .values(*agrup)
                        .distinct()
                    )

                    for rc in registros_contabeis:

                        key = tuple()
                        for ag in agrupamento:
                            key += (rc[ag] or "",)
                        if key not in groups:
                            groups[key] = {
                                "emendas": OrderedDict(),
                                "soma_valor": Decimal("0.00"),
                                "soma_agrupado": Decimal("0.00"),
                            }

                        emenda = emendas_dict.get(rc["emendaloa"])
                        if not emenda:
                            continue

                        # LOA-LST-055: a emenda entra uma vez na soma das emendas
                        # do grupo, mesmo com mais de um registro nele
                        if rc["emendaloa"] not in groups[key]["emendas"]:
                            groups[key]["emendas"][rc["emendaloa"]] = emenda
                            groups[key]["soma_valor"] += emenda.valor
                        groups[key]["soma_agrupado"] += rc["valor"]

                else:
                    # LOA-LST-057: emenda sem unidade ou sem entidade fica num
                    # grupo com a dimensão vazia, mostrada como "Sem ..."
                    dimensoes = [
                        d
                        for d in ("despesa__unidade", "entidade")
                        if d in cd["agrupamento"]
                    ]
                    for emenda in self.object_list:
                        key = []
                        if "despesa__unidade" in cd["agrupamento"]:
                            if emenda.unidade:
                                key = [
                                    emenda.unidade.codigo,
                                    emenda.unidade.especificacao,
                                ]
                            else:
                                key = ["", ""]
                        if "entidade" in cd["agrupamento"]:
                            if emenda.entidade:
                                cpfcnpj = re.sub(
                                    r"[0\s]", "", emenda.entidade.cpfcnpj or ""
                                )
                                if cpfcnpj:
                                    cpfcnpj = emenda.entidade.cpfcnpj
                                key += [
                                    f"{cpfcnpj or emenda.entidade.cnes}",
                                    emenda.entidade.nome_fantasia,
                                ]
                            else:
                                key += ["", ""]

                        key = tuple(key)
                        if not key:
                            continue
                        if key not in groups:
                            groups[key] = {
                                "emendas": OrderedDict(),
                                "soma_valor": Decimal("0.00"),
                                "soma_agrupado": Decimal("0.00"),
                            }
                        groups[key]["emendas"][emenda.id] = emenda
                        groups[key]["soma_valor"] += emenda.valor

                def dimensao_vazia(key):
                    return any(
                        not key[i] and not key[i + 1] for i in range(0, len(key), 2)
                    )

                # LOA-LST-058: grupos com alguma dimensão vazia vão para o fim
                keys = sorted(groups.keys(), key=lambda x: (dimensao_vazia(x), x[::-1]))
                groups_completo = {key: groups[key] for key in keys}

                emendas_no_total = set()
                for key, cd_group in groups_completo.items():
                    title_parts = []
                    for i in range(0, len(key), 2):
                        if key[i] or key[i + 1]:
                            title_parts.append((key[i], key[i + 1]))
                        else:
                            rotulo = ROTULO_SEM_DIMENSAO.get(dimensoes[i // 2], "")
                            title_parts.append(("", f"Sem {rotulo}".strip()))

                    codigo, titulo = zip(*title_parts)
                    max_lenght_codigo = max(map(len, codigo))
                    codigo = list(
                        map(
                            lambda x: escape(x.rjust(max_lenght_codigo, " ")),
                            codigo,
                        )
                    )
                    codigo = list(map(lambda x: x.replace(" ", "&nbsp;"), codigo))
                    title_parts = []
                    for i in range(len(codigo)):
                        title_parts.append(
                            f"<strong>{codigo[i]}</strong> - {escape(titulo[i])}"
                        )

                    title = "<br>".join(title_parts)

                    columns = ["Emendas", "Valores das Emendas"]

                    # if not cd['tipo'] or len(cd['tipo']) > 1:
                    #    columns.insert(1, 'Tipos')

                    sub_total_emendas = cd_group["soma_valor"].quantize(Decimal("0.01"))
                    sub_total_agrupado = cd_group["soma_agrupado"].quantize(
                        Decimal("0.01")
                    )

                    movimentacao_valores = Decimal("0.00")
                    rows = []
                    cd_group["emendas"] = dict(
                        sorted(
                            cd_group["emendas"].items(),
                            key=lambda x: (
                                x[1].materia.numero
                                if x[1].materia and x[1].materia.numero
                                else 0
                            ),
                        )
                    )
                    for item in cd_group["emendas"].values():
                        # LOA-LST-062: o Total soma cada emenda listada uma única
                        # vez, mesmo que ela apareça em mais de um grupo
                        if item.id not in emendas_no_total:
                            emendas_no_total.add(item.id)
                            total += item.valor

                        cols = []
                        rows.append(cols)

                        col_emenda = render_col_emenda(
                            item,
                        )
                        cols.append([col_emenda, ""])

                        # if not cd['tipo'] or len(cd['tipo']) > 1:
                        #    cols.append(
                        #        (item.get_tipo_display(), 'text-center'))

                        cols.append([item.str_valor, "text-right"])

                        qs_rc = item.registrocontabil_set.order_by("valor")

                        registros = []
                        max_lenght_valor = 0
                        for rc in qs_rc:
                            rc = escape(str(rc)).split(" - ")
                            rc[0] = list(filter(lambda x: x, rc[0].split(" ")))
                            if "-" not in rc[0][-1]:
                                rc[0][-1] = f"+{rc[0][-1]}"
                            rc[0] = " ".join(rc[0])
                            if len(rc[0]) > max_lenght_valor:
                                max_lenght_valor = len(rc[0])
                            registros.append(rc)

                        for index, rc in enumerate(registros):
                            rc[0] = alinhar_valor(rc[0], max_lenght_valor)
                            rc[0] = rc[0].replace(" ", "&nbsp;")
                            registros[index] = f'<li>{" - ".join(rc)}</li>'

                        if registros:
                            cols[0][0] = cols[0][0].replace(
                                "<ul></ul>",
                                f'<small class="courier"><small>DOTAÇÕES ORÇAMENTÁRIAS DE ORIGEM(-) E DESTINO(+):</small></small><ul>{"".join(registros)}</ul>',
                            )

                    # LOA-LST-061: orçamento, movimentação e saldo só são
                    # exibidos (e calculados) nas vias de inserção e de dedução
                    soma_valor_orcamento = Decimal("0.00")
                    if cd["tipo_agrupamento"] != "sem_registro":
                        agrupamento_soma = list(
                            filter(
                                lambda x: x,
                                map(
                                    lambda x: "__".join(x.split("__")[1:]),
                                    agrupamento,
                                ),
                            )
                        )

                        soma_valor_orcamento = (
                            Despesa.objects.filter(
                                loa=self.loa, **dict(zip(agrupamento_soma, key))
                            )
                            .order_by(*agrupamento_soma)
                            .distinct()
                            .aggregate(Sum("valor_materia"))
                        )
                        soma_valor_orcamento = soma_valor_orcamento.get(
                            "valor_materia__sum"
                        ) or Decimal("0.00")

                        params = dict(zip(agrupamento, key))
                        params.pop("entidade", None)
                        agrupset = list(
                            set(agrupamento)
                            - set(
                                [
                                    "entidade",
                                ]
                            )
                        )
                        # LOA-LST-061: a emenda transformada em coletiva (fase
                        # -10) mantém os registros, que a coletiva repete
                        movimentacao_valores = EmendaLoaRegistroContabil.objects.filter(
                            emendaloa__loa=self.loa, emendaloa__fase__gt=0, **params
                        ).order_by(*agrupset).aggregate(Sum("valor")).get(
                            "valor__sum"
                        ) or Decimal(
                            "0.00"
                        )

                    group = {
                        "title": title,
                        "columns": columns,
                        "ncols_menos2": len(columns) - 2,
                        "ncols_menos1": len(columns) - 1,
                        "rows": rows,
                        "soma_valor_orcamento": formats.number_format(
                            soma_valor_orcamento, force_grouping=True
                        ),
                        "saldo_orcamento": formats.number_format(
                            soma_valor_orcamento + movimentacao_valores,
                            force_grouping=True,
                        ),
                        "movimentacao_valores": formats.number_format(
                            movimentacao_valores, force_grouping=True
                        ),
                        "sub_total_emendas": formats.number_format(
                            sub_total_emendas, force_grouping=True
                        ),
                        "sub_total_agrupado": formats.number_format(
                            sub_total_agrupado, force_grouping=True
                        ),
                        "agrupamento": True,
                    }
                    context["groups"].append(group)
            context["total"] = formats.number_format(total, force_grouping=True)

            return context

        def get_filterset_kwargs(self, filterset_class):
            kw = FilterView.get_filterset_kwargs(self, filterset_class)
            kw["loa"] = self.loa
            return kw

        def get_queryset(self):
            qs = EmendaLoa.service.visiveis(self.request.user, super().get_queryset())
            return qs.order_by("-tipo", "fase", "materia__numero", "-id")

        def get_context_data(self, **kwargs):
            context = MasterDetailCrud.ListView.get_context_data(self, **kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} emendaloa-list"
            context["type_pagination"] = "pagination-static"
            context.pop("title")

            return context

    class CreateView(MasterDetailCrud.CreateView):
        layout_key = None
        form_class = EmendaLoaForm

        def get_context_data(self, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs["root_pk"])
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} emendaloa-create"
            return context

        def get_success_url(self):
            return self.update_url

        @property
        def cancel_url(self):
            url = super().cancel_url
            if not url and self.request.user.operadorautor_set.exists():
                url = self.resolve_url("list", args=(self.kwargs["pk"],))
            return url

        def has_permission(self):

            u = self.request.user
            if u.is_anonymous:
                return False

            has_perm = MasterDetailCrud.CreateView.has_permission(self)

            self.loa = Loa.objects.get(pk=self.kwargs["pk"])

            # LOA-EMD-082: operador de autor cria, publicada ou não a LOA
            return has_perm or EmendaLoa.service.pode_criar(u)

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = self.loa
            initial["user"] = self.request.user
            initial["creating"] = True
            return initial

        def form_invalid(self, form):
            r = MasterDetailCrud.CreateView.form_invalid(self, form)

            err_materia = form.errors.get("materia", None)
            if err_materia:
                err_materia = "Já existe registro de valores para a Matéria Legislativa selecionada."

                self.messages.error(err_materia, fail_silently=True)
            return r

    class UpdateView(MasterDetailCrud.UpdateView):
        layout_key = None
        form_class = EmendaLoaForm
        permission_required = ("loa.emendaloa_full_editor",)

        def get_context_data(self, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs["root_pk"])
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} emendaloa-update"
            # context['fluid'] ='-fluid'

            return context

        def get_success_url(self):
            return MasterDetailCrud.UpdateView.get_success_url(self)

        @property
        def edita_em_qualquer_fase(self):
            # superusuário e quem tem as permissões do grupo Operador da LOA
            return EmendaLoa.edita_em_qualquer_fase(self.request.user)

        def post(self, request, *args, **kwargs):
            u = request.user
            if not u.is_anonymous and not self.edita_em_qualquer_fase:
                if u.operadorautor_set.exists():
                    if (
                        self.object.fase > EmendaLoa.PROPOSTA_LIBERADA
                        and self.object.fase != EmendaLoa.LIBERACAO_CONTABIL
                    ):
                        messages.warning(
                            request,
                            f'A Emenda está na fase de "{self.object.get_fase_display()}". Não pode ser editada por usuário de autoria.',
                        )
                        return redirect(self.detail_url)

            return MasterDetailCrud.UpdateView.post(self, request, *args, **kwargs)

        def form_valid(self, form):
            u = self.request.user
            if u.has_perm("loa.emendaloa_full_editor"):
                submit_concluir = "submit_concluir" in self.request.POST
                submit_devolver = "submit_devolver" in self.request.POST
                if submit_concluir or submit_devolver:
                    # LOA-FASE-063 e 069: os botões só agem nas fases 15 e 17.
                    # form.initial guarda a fase gravada; form.instance já recebeu a do POST.
                    fase_origem = form.initial.get("fase")
                    if fase_origem not in EmendaLoa.FASES_DOS_BOTOES_CONTABEIS:
                        fases = dict(EmendaLoa.FASE_CHOICE)
                        form.add_error(
                            None,
                            "Concluir ou devolver só é possível nas fases "
                            f'"{fases[EmendaLoa.EDICAO_CONTABIL]}" e '
                            f'"{fases[EmendaLoa.LIBERACAO_CONTABIL]}".',
                        )
                        return self.form_invalid(form)
                    if submit_devolver:  # LOA-FASE-072
                        try:
                            EmendaLoa.service.validar_fase_da_coletiva(
                                form.instance, EmendaLoa.PROPOSTA
                            )
                        except ValidationError as e:
                            form.add_error(None, e.messages)
                            return self.form_invalid(form)
                    form.instance.fase = (
                        EmendaLoa.LIBERACAO_CONTABIL
                        if submit_concluir
                        else EmendaLoa.PROPOSTA
                    )

            return super().form_valid(form)

        def get(self, request, *args, **kwargs):
            u = request.user

            if (
                u.has_perm("loa.emendaloa_full_editor")
                and not u.is_superuser  # LOA-FASE-066: captura só para o editor contábil
                and EmendaLoa.PROPOSTA_LIBERADA
                <= self.object.fase
                <= EmendaLoa.LIBERACAO_CONTABIL
            ):
                if self.object.fase == EmendaLoa.PROPOSTA_LIBERADA:
                    self.object.fase = EmendaLoa.EDICAO_CONTABIL
                    self.object._usuario_fase = u  # LOA-FASE-067
                    self.object.save()

            elif not self.edita_em_qualquer_fase:
                if (
                    not u.is_superuser
                    and self.object.fase > EmendaLoa.LIBERACAO_CONTABIL
                ):
                    messages.warning(
                        request,
                        f'A Emenda está na fase de "{self.object.get_fase_display()}". Não pode ser editada por usuário de autoria.',
                    )
                    return redirect(self.detail_url)

                if not u.is_superuser:
                    # LOA-EMD-076
                    if not EmendaLoa.service.e_autor_da_emenda(u, self.object):
                        messages.warning(
                            request,
                            f"Apenas o usuário ligado ao cadastro pode editar esta emenda.",
                        )
                        return redirect(self.detail_url)

                if (
                    self.object.fase > EmendaLoa.PROPOSTA_LIBERADA
                    and self.object.fase < EmendaLoa.LIBERACAO_CONTABIL
                ):
                    messages.warning(
                        request,
                        f'A Emenda está na fase de "{self.object.get_fase_display()}". Não pode ser editada por usuário de autoria.',
                    )
                    return redirect(self.detail_url)

            return MasterDetailCrud.UpdateView.get(self, request, *args, **kwargs)

        def has_permission(self):
            u = self.request.user
            if u.is_anonymous:
                return False

            has_perm = MasterDetailCrud.UpdateView.has_permission(self)

            self.object = (
                self.get_object() if not hasattr(self, "object") else self.object
            )

            if has_perm:
                return True

            # LOA-EMD-076: só o autor do dono; coautores só consultam (resolve D7)
            return EmendaLoa.service.e_autor_da_emenda(u, self.object)

        def get_initial(self):
            initial = super().get_initial()
            initial["loa"] = self.object.loa
            initial["user"] = self.request.user
            initial["creating"] = False
            if self.object.materia:
                initial["tipo_materia"] = self.object.materia.tipo.id
                initial["numero_materia"] = self.object.materia.numero
                initial["ano_materia"] = self.object.materia.ano
            return initial

        @property
        def cancel_url(self):
            url = self.resolve_url("detail", args=(self.kwargs["pk"],))
            return url

    class DetailView(MasterDetailCrud.DetailView):

        @property
        def layout_key(self):
            return "EmendaLoaDetail"

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} emendaloa-detail"
            title = f"""{self.object.materia.epigrafe_short + ' - ' if self.object.materia else ''}
            R$ { self.object.str_valor } -
            { self.object.entidade.nome_fantasia if self.object.entidade else ''}
            {self.object.unidade.especificacao if not self.object.entidade and self.object.unidade else ''}
            <small>{'<br>' + str(self.object) if not self.object.materia else ''}</small>
            <br><small>({self.object.loa})</small>

            """
            context["title"] = title.replace("\n", "")

            return context

        def hook_owner(self, el, verbose_name="", field_display=""):
            if self.request.user.is_anonymous:
                return "", ""
            return verbose_name, field_display

        def hook_str_valor_computado(self, el, verbose_name="", field_display=""):
            if not el.materia:
                return "", ""

            return (
                "Valor Final da Emenda (R$)",
                field_display,
                "form-control-static text-blue text-nowrap text-center font-weight-bold zoom-2",
            )

        def hook_tipo(self, el, verbose_name="", field_display=""):
            if el.tipo:
                return verbose_name, field_display

            return "Emenda Modificativa", "Emenda Modificativa"

        def hook_fase(self, el, verbose_name="", field_display=""):
            classes = "form-control-static text-center font-weight-bold"
            if el.fase == EmendaLoa.IMPEDIMENTO_TECNICO:
                return verbose_name, field_display, f"{classes} text-danger"
            return verbose_name, field_display, classes

        def hook_indicacao(self, el, verbose_name="", field_display=""):
            return f"{verbose_name} (Unidade Orçamentária)", field_display

        def hook_finalidade(self, el, verbose_name="", field_display=""):
            return (
                verbose_name,
                (
                    el.finalidade_format
                    if not el.has_ajustes
                    else f"""
                    <span class="d-block text-gray" style="text-decoration: line-through;">{el.finalidade_format}</span>
                    <span class="badge badge-warning">Finalidade atualizada conforme Registro de Ajuste Técnico</span>
                    """
                ),
            )

        def hook_materia(self, el, verbose_name="", field_display=""):
            if not el.materia:
                return "", ""

            strm = str(el.materia)
            field_display = field_display.replace(strm, el.materia.epigrafe_short)
            return (
                "Processo Legislativo da Emenda Impositiva",
                f"""
                Arquivo PDF: <a href="{el.materia.texto_original.url}" class="btn btn-link" title="Arquivo PDF da Emenda no Processo Legislativo"><i class="fa-solid fa-file-pdf "></i></a>
                | Processo Legislativo: <a href="{reverse_lazy('sapl.materia:materialegislativa_detail', kwargs={'pk': el.materia.id})}">
                    {field_display}
                </a>""",
            )

        def hook_registroajusteloa_set(self, el, verbose_name="", field_display=""):

            if not el.materia:
                return "", ""

            if not el.has_ajustes:
                return (
                    verbose_name,
                    "Esta Emenda não possui registros de Ajuste Técnico",
                )

            ajustes = []
            for ajuste in el.registroajusteloa_set.all():
                url = reverse_lazy(
                    "cmj.loa:registroajusteloa_detail", kwargs={"pk": ajuste.id}
                )

                a_str = f"""
                    <li>
                        <a href="{url}">
                            {ajuste}
                        </a>
                        <small class="text-gray d-block">{ajuste.descricao}</small>
                    </li>
                """
                ajustes.append(a_str)

            return verbose_name, f'<ul>{"".join(ajustes)}</ul>'

        def hook_documentos_acessorios(self, el, verbose_name="", field_display=""):

            if not el.materia or not el.materia.documentoacessorio_set.exists():
                return "", ""

            docs = []

            qs_docs = (
                []
                if not el.materia
                else el.materia.documentoacessorio_set.order_by("-data")
            )
            for doc in qs_docs:
                doc_template = loader.get_template(
                    "materia/documentoacessorio_widget_itemlist.html"
                )
                context = {}
                context["object"] = doc
                rendered = doc_template.render(context, self.request)

                docs.append(f"<tr><td>{rendered}</td></tr>")
            if not docs:
                return (
                    verbose_name,
                    "Esta Emenda não possui outros documentos acessórios cadastrados ao Processo Legislativo",
                )

            return (
                "Documentos Acessórios vinculados ao Processo Legislativo",
                f"""
                <div class="container-table m-0 mx-n3">
                    <table class="table table-form table-bordered table-hover w-100">
                        {"".join(docs)}
                    </table>
                </div>
                """,
            )

        def hook_prestacaocontaregistro_set(
            self, emendaloa, verbose_name="", field_display=""
        ):

            if not emendaloa.materia:
                return "", ""

            pcs = []

            for pc in emendaloa.prestacaocontaregistro_set.all():
                pc_url = reverse_lazy(
                    "cmj.loa:prestacaocontaregistro_detail", kwargs={"pk": pc.id}
                )
                pcs.append(f"""<li>
                        <span class="badge badge-secondary">{formats.date_format(pc.prestacao_conta.data_envio, "SHORT_DATE_FORMAT")}</span>
                        <span class="badge badge-secondary">{pc.situacao}</span>
                        <a href="{ pc_url}" class="d-inline-block font-weight-bold pt-1">
                        {pc.prestacao_conta}
                        </a>
                        <span class="text-gray d-block">{pc.detalhamento}</span>
                    </li>""")

            if not pcs:
                return (
                    verbose_name,
                    "Esta Emenda não possui registros de Prestação de Contas",
                )

            return (
                "Registros de Prestação de Contas",
                f"""
                <ul>
                    {"".join(pcs)}
                </ul>
                """,
                "bg-light",
            )

        def hook_registrocontabil_set(
            self, emendaloa, verbose_name="", field_display=""
        ):
            # renderizar com ul e li
            rcs = []
            for rc in emendaloa.registrocontabil_set.all():
                rcs.append(
                    f"""<li {'class="text-gray" style="text-decoration: line-through;"' if emendaloa.has_ajustes else ''}>
                            {rc}
                    </li>"""
                )
            if not rcs:
                return (
                    verbose_name,
                    "Esta Emenda não possui registros contábeis de inserção ou retirada de recursos.",
                )
            return (
                verbose_name,
                f"""
                <ul>
                    {"".join(rcs)}
                </ul>
                """,
                f"form-control-static",
            )

        def hook_parlamentares(self, emendaloa, verbose_name="", field_display=""):
            pls = []

            for elp in emendaloa.emendaloaparlamentar_set.all():
                if elp.emendaloa.tipo:
                    pls.append(
                        '<tr><td>{}</td><td align="right">R$ {}</td></tr>'.format(
                            elp.parlamentar.nome_parlamentar,
                            formats.number_format(elp.valor, force_grouping=True),
                        )
                    )
                else:
                    pls.append(f"<tr><td>{elp.parlamentar.nome_parlamentar}</td>")

            return (
                verbose_name,
                f"""
                <div class="py-3">
                    <table class="table table-form table-bordered table-hover w-100">
                        {"".join(pls)}
                    </table>
                </div>
                """,
            )

        def hook_emendaloahistoricofase_set(
            self, emendaloa, verbose_name="", field_display=""
        ):
            if not self.request.user.is_superuser:
                return "", ""

            lines = []
            historico = emendaloa.emendaloahistoricofase_set.select_related("usuario")
            for ehf in historico.order_by("-id"):
                # LOA-FASE-067: registros antigos e mudanças automáticas não têm usuário
                usuario = escape(str(ehf.usuario)) if ehf.usuario else "—"
                lines.append(
                    f"{ehf.id} - {ehf.timestamp} - {ehf.get_fase_display()}"
                    f" - {usuario}<br>"
                )

            return verbose_name, "".join(lines), "courier"

        def hook_auditlog(self, emendaloa, verbose_name="", field_display=""):
            if not self.request.user.is_superuser:
                return "", ""
            cts = list(
                ContentType.objects.get_for_models(
                    EmendaLoa, EmendaLoaRegistroContabil, EmendaLoaParlamentar
                ).values()
            )

            al_create = (
                AuditLog.objects.filter(
                    content_type=cts[0],
                    object_id=emendaloa.id,
                )
                .order_by("id")
                .first()
            )
            if not al_create:
                return "", ""

            q = Q()
            q |= Q(obj_id=emendaloa.id, model_name="emendaloa")
            q |= Q(obj__0__fields__emendaloa=emendaloa.id)
            models_name = list(map(lambda ct: ct.model, cts))
            als = AuditLog.objects.filter(q, model_name__in=models_name).order_by("id")

            result = dict(
                emendaloa=[], emendaloaparlamentar=[], emendaloaregistrocontabil=[]
            )

            last_fields = dict(
                emendaloa=None,
                emendaloaparlamentar=None,
                emendaloaregistrocontabil=None,
            )

            for al in als:

                fields = al.obj[0]["fields"]

                if fields != last_fields[al.model_name] or al.operation in ("C", "D"):
                    result[al.model_name].append(al)
                    last_fields[al.model_name] = fields

            results = []
            for k, als in result.items():
                results.extend(als)

            results = sorted(results, key=lambda al: -al.id)

            lines = []
            for al in results:
                lines.append(
                    f"{al.timestamp} - {al.operation} - "
                    f'{al.content_type} - {al.user} - {al.obj[0]["pk"]} - {al.obj[0]["fields"]}<br>'
                )

            return verbose_name, "".join(lines)

        def hook_empenhoemendaajuste_set(
            self, emendaloa, verbose_name="", field_display=""
        ):
            empenhos = []
            for eea in emendaloa.empenhoemendaajuste_set.order_by(
                "-empenho__codigo"
            ).select_related("empenho"):
                empenho = eea.empenho
                url = reverse_lazy("cmj.loa:empenho_detail", kwargs={"pk": empenho.id})
                empenhos.append(f"""
                    <li>
                        <a href="{url}">{empenho.codigo}</a> |
                            {formats.date_format(empenho.data, "SHORT_DATE_FORMAT")} |
                            R$ {empenho.str_valor_empenhado} |
                            {empenho.nome}
                    </li>""")
            return (
                "Empenhos da Emenda",
                f'<ul class="small courier">{"".join(empenhos)}</ul>',
            )
