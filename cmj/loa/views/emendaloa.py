import io
import re
import tempfile
import zipfile
from decimal import Decimal
from urllib.parse import urlencode

import fitz
import requests
from _collections import OrderedDict
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files import File
from django.db.models import Max, Q
from django.db.models.aggregates import Sum
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.template.loader import render_to_string
from django.urls.base import reverse, reverse_lazy
from django.utils import formats, timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from cmj.core.models import AuditLog
from cmj.loa import tasks
from cmj.loa.forms import EmendaLoaFilterSet, EmendaLoaForm
from cmj.loa.models import (
    Despesa,
    EmendaLoa,
    EmendaLoaParlamentar,
    EmendaLoaRegistroContabil,
    Loa,
)
from cmj.loa.views.mixins import LoaContextDataMixin
from cmj.utils import TimeExecution
from cmj.utils_report import make_pdf
from sapl.crud.base import RP_DETAIL, RP_LIST, MasterDetailCrud
from sapl.materia.models import Proposicao, TipoProposicao
from sapl.parlamentares.models import Parlamentar
from sapl.utils import get_client_ip


class EmendaLoaCrud(MasterDetailCrud):
    model = EmendaLoa
    parent_field = "loa"
    public = [RP_LIST, RP_DETAIL]
    frontend = EmendaLoa._meta.app_label

    class BaseMixin(LoaContextDataMixin, MasterDetailCrud.BaseMixin):
        list_field_names = [("id",)]
        """list_field_names = [
            ("finalidade"),
            "str_valor_computado",
            ("tipo", "fase"),
            "parlamentares",
        ]"""

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
            elif (
                self.request.user.operadorautor_set.exists()
                and EmendaLoa.PROPOSTA <= self.object.fase < EmendaLoa.EM_TRAMITACAO
                and self.object.parlamentares.filter(
                    id__in=self.request.user.operadorautor_set.values_list(
                        "autor__object_id", flat=True
                    )
                ).exists()
            ):
                return url_perm

            return ""

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

    class ListView(FilterView, MasterDetailCrud.ListView):
        filterset_class = EmendaLoaFilterSet

        @property
        def extras_url(self):
            if (
                self.request.user.is_anonymous
                or not self.request.user.operadorautor_set.exists()
            ):
                return []

            if (
                not self.get_emendas_criadas_por_operador_mesmo_autor()
                .filter(fase__gte=EmendaLoa.LIBERACAO_CONTABIL)
                .exists()
            ):
                return []

            btns = []
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
                (
                    reverse_lazy(
                        "cmj.loa:emendaloa_list", kwargs={"pk": self.kwargs["pk"]}
                    )
                    + "?register",
                    "btn-warning btn-register-emendas-liberadas",
                    """<span title="Registrar todas as emendas Liberadas no módulo de proposições. Emendas já registradas serão atualizadas se ainda não enviadas ao protocolo.">
                        <i class="fas fa-file-contract"></i> Registrar Emendas Liberadas</span>
                    """,
                ),
            ]

        def get_emendas_criadas_por_operador_mesmo_autor(self):
            if self.request.user.is_anonymous:
                return self.get_queryset().none()
            autor_operado = self.request.user.operadorautor_set.values_list(
                "autor", flat=True
            )
            OperadorAutor = autor_operado.model

            return self.get_queryset().filter(
                loa=self.loa,
                owner__id__in=OperadorAutor.objects.filter(
                    autor__in=autor_operado
                ).values_list("user", flat=True),
            )

        @property
        def title(self):
            return f"""Emendas Impositivas/Modificativas à LOA {self.loa.ano} <small>({self.loa.materia.epigrafe_short if self.loa.materia else ''})</small>
                """

        def get(self, request, *args, **kwargs):
            self.loa = Loa.objects.get(pk=kwargs["pk"])
            if "register" in self.request.GET:

                from sapl.base.models import OperadorAutor

                # verifica se existe emenda desse usuario que está com metadata setado para register

                if request.user.is_anonymous:
                    messages.warning(
                        self.request, "Ação não permitida para usuários anônimos."
                    )
                    return redirect(
                        reverse_lazy(
                            "cmj.loa:emendaloa_list", kwargs={"pk": self.loa.id}
                        )
                    )

                user_id = request.user.id

                autor_operado = OperadorAutor.objects.filter(user_id=user_id).first()
                if not autor_operado:
                    messages.warning(
                        self.request,
                        "Ação não permitida. Usuário não é operador de nenhum autor parlamentar.",
                    )

                    return redirect(
                        reverse_lazy(
                            "cmj.loa:emendaloa_list", kwargs={"pk": self.loa.id}
                        )
                    )

                autor_operado = autor_operado.autor
                operadores = OperadorAutor.objects.filter(
                    autor=autor_operado
                ).values_list("user_id", flat=True)

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
                return redirect(reverse_lazy("sapl.materia:proposicao_list"))

            return FilterView.get(self, request, *args, **kwargs)

        def render_to_response(self, context, **response_kwargs):
            if "pdf" in self.request.GET:
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

            req = self.request
            base_url = f"{req.scheme}://{req.get_host()}"

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

                    for emenda in emendas:
                        response = requests.get(
                            f"{base_url}/api/loa/emendaloa/{emenda.id}/view/"
                        )

                        if response.status_code == 200:
                            nome_emenda = f"emendaloa_{emenda.id}_sem_vinculo_com_proposicao_{emenda.loa.ano}"
                            if emenda.materia:
                                nome_emenda = f"emendaloa_{emenda.id}_ja_procolocada_{emenda.materia.tipo.sigla}_{emenda.materia.numero}_{emenda.materia.ano}"
                            elif emenda.proposicao:
                                nome_emenda = f"emendaloa_{emenda.id}_com_proposicao_gerada_{emenda.proposicao.tipo.descricao}_{emenda.proposicao.numero_proposicao}_{emenda.proposicao.ano}"
                            nome_emenda = slugify(nome_emenda)

                            file.writestr(f"{nome_emenda}.pdf", response.content)
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
            base_url = self.request.build_absolute_uri()
            with TimeExecution(
                print_date=settings.DEBUG, label="Make Context PDF EmendaLoa List"
            ):
                try:
                    context = self.get_context_data_makepdf()
                except:
                    raise ValidationError(
                        "Ocorreu um erro ao processar seus filtros e agrupamentos."
                    )

            # context['groups'][0]['rows'] = context['groups'][0]['rows'][:10]

            with TimeExecution(
                print_date=settings.DEBUG, label="Render Html EmendaLoa List"
            ):
                template = render_to_string("loa/pdf/emendaloa_list.html", context)

            with TimeExecution(
                print_date=settings.DEBUG, label="Generate PDF EmendaLoa List"
            ):
                pdf_file = make_pdf(base_url=base_url, main_template=template)

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
                filtro = f'<strong>Parlamentares:</strong> {" / ".join(map(lambda x: str(x), cd["parlamentares"]))}'
                filters.append(filtro)

            if cd.get("finalidade", ""):
                filtro = f'<strong>Finalidade:</strong> {cd["finalidade"]}'
                filters.append(filtro)

            if cd.get("tipo", ""):
                dt = dict(
                    map(lambda x: (str(x[0]), x[1]), EmendaLoa.TIPOEMENDALOA_CHOICE)
                )
                filtro = f'<strong>Tipos de Emenda:</strong> {" / ".join(map(lambda x: str(dt[x]), cd["tipo"]))}'
                filters.append(filtro)

            if cd.get("fase", ""):
                dt = dict(map(lambda x: (str(x[0]), x[1]), EmendaLoa.FASE_CHOICE))
                filtro = f'<strong>Fases de Emenda:</strong> {" / ".join(map(lambda x: str(dt[x]), cd["fase"]))}'
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
                                {item.materia.epigrafe_short}
                                </a>
                            </span>
                    """
                else:
                    materia = f"""
                            <span class="materia">
                                <a href="{reverse('cmj.loa:emendaloa_detail',kwargs={'pk': item.id})}">
                                Emenda Parlamentar em construção
                                </a>
                            </span>
                    """

                autores = f"""
                    <small>
                        <strong>Autoria:</strong> {' - '.join(map(lambda x: str(x), item.parlamentares.all()))}
                    </small>
                """

                col_emenda = f"""

                    <div class="loa-mat">
                        <div class="row">
                            <div class="col">
                                {materia}
                                { '&nbsp;-&nbsp;' if item.parlamentares.count() <= 3 else '' }
                                { autores if item.parlamentares.count() <= 3 else ''}
                            </div>
                            <div class="col">
                                <span>Tipo:</span>&nbsp;
                                <strong class="tipo">{item.get_tipo_display()}</strong>
                            </div>
                        </div>
                        { autores if item.parlamentares.count() > 3 else ''}
                        { '<br>' if item.parlamentares.count() > 3 else ''}
                        <span class="indicacao">{item.indicacao}</span>
                        <div>
                            {item.finalidade_format}
                        </div>
                        <ul></ul>
                    </div>
                """
                return col_emenda

            total = Decimal("0.00")
            self.object_list = self.object_list.order_by("materia__numero")
            if not cd.get("agrupamento", []):

                if not self.object_list.exists():
                    return context

                context["title"] = context["title"].replace("{}", "")

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
                            key += (rc[ag],)
                        if key not in groups:
                            groups[key] = {
                                "emendas": OrderedDict(),
                                "soma_valor": Decimal("0.00"),
                                "soma_agrupado": Decimal("0.00"),
                            }

                        emenda = emendas_dict.get(rc["emendaloa"])
                        if not emenda:
                            continue

                        if rc["emendaloa"] not in groups[key]["emendas"]:
                            groups[key]["emendas"][rc["emendaloa"]] = emenda
                        groups[key]["soma_agrupado"] += rc["valor"]
                        groups[key]["soma_valor"] += emenda.valor

                else:
                    for emenda in self.object_list:
                        key = []
                        if "despesa__unidade" in cd["agrupamento"]:
                            key = [emenda.unidade.codigo, emenda.unidade.especificacao]
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
                                if "despesa__unidade" in cd["agrupamento"]:
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

                keys = list(groups.keys())
                keys.sort(key=lambda x: x[::-1])
                groups_completo = {key: groups[key] for key in keys if key[-1]}
                groups_completo.update(
                    {key: groups[key] for key in keys if not key[-1]}
                )

                for key, cd_group in groups_completo.items():
                    title_parts = []
                    for i in range(0, len(agrupamento), 2):
                        part = key[i]
                        if part:
                            title_parts.append((part, key[i + 1]))

                    try:
                        codigo, titulo = zip(*title_parts)
                    except Exception as e:
                        print(e)
                        continue
                    max_lenght_codigo = max(map(len, codigo))
                    codigo = list(
                        map(lambda x: x.rjust(max_lenght_codigo, " "), codigo)
                    )
                    codigo = list(map(lambda x: x.replace(" ", "&nbsp;"), codigo))
                    title_parts = []
                    for i in range(len(codigo)):
                        title_parts.append(
                            f"<strong>{codigo[i]}</strong> - {titulo[i]}"
                        )

                    title = "<br>".join(title_parts)

                    columns = ["Emendas", "Valores das Emendas"]

                    # if not cd['tipo'] or len(cd['tipo']) > 1:
                    #    columns.insert(1, 'Tipos')

                    sub_total_emendas = cd_group["soma_valor"].quantize(Decimal("0.01"))
                    sub_total_agrupado = cd_group["soma_agrupado"].quantize(
                        Decimal("0.01")
                    )

                    if cd["tipo_agrupamento"] != "sem_registro":
                        total += sub_total_agrupado
                    else:
                        total += sub_total_emendas

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
                            rc = str(rc).split(" - ")
                            rc[0] = list(filter(lambda x: x, rc[0].split(" ")))
                            if "-" not in rc[0][-1]:
                                rc[0][-1] = f"+{rc[0][-1]}"
                            rc[0] = " ".join(rc[0])
                            if len(rc[0]) > max_lenght_valor:
                                max_lenght_valor = len(rc[0])
                            registros.append(rc)

                        for index, rc in enumerate(registros):
                            while len(rc[0]) < max_lenght_valor:
                                rc[0] = rc[0].replace(" ", "  ", 1)
                            rc[0] = rc[0].replace(" ", "&nbsp;")
                            registros[index] = f'<li>{" - ".join(rc)}</li>'

                        if registros:
                            cols[0][0] = cols[0][0].replace(
                                "<ul></ul>",
                                f'<small class="courier"><small>DOTAÇÕES ORÇAMENTÁRIAS DE ORIGEM(-) E DESTINO(+):</small></small><ul>{"".join(registros)}</ul>',
                            )

                    agrupamento_soma = list(
                        filter(
                            lambda x: x,
                            map(lambda x: "__".join(x.split("__")[1:]), agrupamento),
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
                    movimentacao_valores = EmendaLoaRegistroContabil.objects.filter(
                        emendaloa__loa=self.loa, **params
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
            qs = super().get_queryset()
            if self.request.user.is_anonymous:
                qs = qs.filter(loa__publicado=True)
            return qs.order_by("-tipo", "fase", "materia__numero", "-id")

        def get_context_data(self, **kwargs):
            context = MasterDetailCrud.ListView.get_context_data(self, **kwargs)
            path = context.get("path", "")
            context["path"] = f"{path} emendaloa-list"
            context["type_pagination"] = "pagination-static"

            return context

        def hook_header_str_valor_computado(self, *args, **kwargs):
            return "Valor Final da Emenda" if self.loa.publicado else "Valor da Emenda"

        def hook_str_valor_computado(self, *args, **kwargs):
            return f'<div class="text-nowrap text-center">R$ {args[1]}</div>', args[2]

        def hook_tipo(self, *args, **kwargs):
            el = args[0]
            tipo = args[1] if args[1] else "EMENDA MODIFICATIVA"
            link_pdf = ""
            link_create_proposicao_pre_preenchida = ""
            link_generate_proposicao = ""

            emendas_mesmo_autor = (
                self.get_emendas_criadas_por_operador_mesmo_autor().filter(
                    fase__gte=EmendaLoa.LIBERACAO_CONTABIL
                )
            )
            if not emendas_mesmo_autor.filter(id=el.id).exists():
                return (
                    f"""
                    {link_pdf}
                    <br>{tipo}
                """,
                    args[2],
                )

            if el.fase == EmendaLoa.LIBERACAO_CONTABIL and not el.materia:

                url = reverse_lazy("sapl.api:loa_emendaloa-view", kwargs={"pk": el.id})
                link_pdf = f'<a href="{url}" target="_blank"><i class="far fa-2x fa-file-pdf"></i></a>'

                """params = dict(
                    descricao=el.ementa_format,
                    tipo_materia=el.loa.materia.tipo.id if el.loa.materia else '',
                    numero_materia=el.loa.materia.numero if el.loa.materia else '',
                    ano_materia=el.loa.materia.ano if el.loa.materia else '',
                    tipo=33 if el.tipo != EmendaLoa.MODIFICATIVA else 5,
                )
                query_params = urlencode(params)
                link_create_proposicao_pre_preenchida = f'''
                    <a target="_blank" href="{reverse_lazy('sapl.materia:proposicao_create')}?{query_params}">

                    </a>
                '''
                # {link_create_proposicao_pre_preenchida} <i class="fas fa-2x fa-magic"></i>"""

                title = (
                    "Gerar Proposição Legislativa para esta Emenda Impositiva/Modificativa"
                    if not el.proposicao
                    else f"Atualizar a {el.proposicao} vinculada a esta Emenda Impositiva/Modificativa"
                )
                link_generate_proposicao = f"""
                    <a title="{title}" href="{reverse_lazy('cmj.loa:emendaloa_detail', kwargs={'pk': el.id})}?register" target="_blank" >
                        <i class="fas fa-2x fa-file-contract"></i>
                    </a>
                """

            return (
                f"""
                {link_pdf} &nbsp; &nbsp; &nbsp;

                {link_generate_proposicao}
                <br>{tipo}
            """,
                args[2],
            )

        def hook_fase(self, *args, **kwargs):
            fase_display = f"<br><small>({args[0].get_fase_display()})</small>"
            el = args[0]
            link_pdf = ""
            if el.fase == EmendaLoa.IMPEDIMENTO_TECNICO:
                doc_acessorio = el.materia.documentoacessorio_set.order_by(
                    "data"
                ).first()
                if doc_acessorio:
                    link_pdf = f'<a title="Acesse Impedimento Técnico" href="{doc_acessorio.arquivo.url}"><i class="far fa-2x fa-file-pdf"></i></a>'
                return f"{fase_display}<br>{link_pdf}", args[2]

            return fase_display, args[2]

        def hook_header_finalidade(self, *args, **kwargs):
            return "Descrição da Emenda"

        def hook_finalidade(self, *args, **kwargs):
            emenda, display_base, url = args

            render = []
            materia = emenda.materia
            if materia:
                render.append(
                    f"<small><strong>Matéria Legislativa:</strong> {materia}</small><br>"
                )

            unidade_orcamentaria = emenda.unidade or emenda.indicacao
            if unidade_orcamentaria:
                render.append(
                    f'<small class="text-gray"><strong>Órgão Executor:</strong> {unidade_orcamentaria}</small><br>'
                )

            if emenda.has_ajustes:
                ajustes = []
                for ajuste in emenda.registroajusteloa_set.order_by("-id"):
                    descr = ""
                    # if ajuste.valor <= Decimal('0.00'):
                    descr = ajuste.descricao

                    ajustes.append(
                        f'<li>{ajuste}<small class="text-gray"><br>{descr}</small></li>'
                    )
                ajustes = "".join(ajustes)
                render.append(
                    f"""
                    <hr class="my-1">
                    <small class="px-2 d-block">
                        <strong>Registros de Ajuste Técnico</strong>
                        <ul class="pl-3  m-0">{ajustes}</ul>
                    </small>
                    """
                )
                return "".join(render), url

            registrocontabil_insercao_set = emenda.registrocontabil_set.filter(
                valor__gt=Decimal("0.00")
            )
            if registrocontabil_insercao_set.exists():
                render.append(
                    '<small class="text-gray"><strong>Ação Orçamentária:</strong> '
                )
                acoes = set()
                for rc in registrocontabil_insercao_set:
                    acoes.add(str(rc.despesa.acao))
                render.append("<br>".join(list(acoes)))

                render.append("<br></small>")

            finalidade = emenda.finalidade_format
            finalidade = f"{finalidade[0].upper()}{finalidade[1:]}"
            finalidade = f'<small class="text-gray"><strong>Entidade/Finalidade:</strong> {finalidade}</small><br>'
            render.append(finalidade)

            return "".join(render), url

        def hook_acoes(self, *args, **kwargs):
            emenda = args[0]
            acoes = set()
            for rc in emenda.registrocontabil_set.filter(valor__gt=Decimal("0.00")):
                acoes.add(str(rc.despesa.acao))
            return "<br>".join(acoes), args[2]

        def hook_parlamentares(self, *args, **kwargs):
            pls = []

            for elp in args[0].emendaloaparlamentar_set.all():
                if elp.emendaloa.tipo:
                    pls.append(
                        '<tr><td>{}</td><td align="right">R$ {}</td></tr>'.format(
                            elp.parlamentar.nome_parlamentar,
                            formats.number_format(elp.valor, force_grouping=True),
                        )
                    )
                else:
                    pls.append(f"<tr><td>{elp.parlamentar.nome_parlamentar}</td>")

            ajustes = []
            for ajuste in args[0].registroajusteloa_set.all():
                url = reverse_lazy(
                    "cmj.loa:registroajusteloa_detail",
                    kwargs={"pk": ajuste.id},
                )

                descr = ""
                # if ajuste.valor <= Decimal('0.00'):
                descr = ajuste.descricao

                ajustes.append(
                    f'<li><a href="{url}">{ajuste}</a><small class="text-gray"><br>{descr}</small></li>'
                )

            ajustes = "".join(ajustes)
            if ajustes:
                ajustes = f"""
                    <hr class="my-1">
                    <small class="px-2 d-block">
                        <strong>Registros de Ajuste Técnico</strong>
                        <ul class="pl-3  m-0">{ajustes}</ul>
                    </small>
                """

            return (
                f"""
                    <table class="w-100 text-nowrap">{"".join(pls)}</table>
                    {ajustes}
                    """,
                "",
            )

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

            if not has_perm:
                return u.operadorautor_set.exists() and self.loa.publicado

            return has_perm

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

        def post(self, request, *args, **kwargs):
            u = request.user
            if not u.is_superuser and not u.is_anonymous:
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
                    form.instance.fase = (
                        EmendaLoa.LIBERACAO_CONTABIL
                        if submit_concluir
                        else EmendaLoa.PROPOSTA
                    )

            return super().form_valid(form)

        def get(self, request, *args, **kwargs):
            u = request.user
            if not u.is_superuser and not u.is_anonymous:
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

                if (
                    u.has_perm("loa.emendaloa_full_editor")
                    and self.object.fase == EmendaLoa.PROPOSTA_LIBERADA
                ):
                    self.object.fase = EmendaLoa.EDICAO_CONTABIL
                    self.object.save()

            return MasterDetailCrud.UpdateView.get(self, request, *args, **kwargs)

        def has_permission(self):
            u = self.request.user
            if u.is_anonymous:
                return False

            has_perm = MasterDetailCrud.UpdateView.has_permission(self)

            self.object = (
                self.get_object() if not hasattr(self, "object") else self.object
            )

            if not has_perm:
                # 1) possui permissão: emendaloa_full_editor
                # 2) é um usuário operador de autor
                # 3) a emenda em edição está na fase de Proposta Legislativa
                # 4) participa da emenda
                # (1 or 2) e 3 e 4

                participa = False
                if u.operadorautor_set.exists():
                    parlamentar = u.operadorautor_set.first().autor.autor_related
                    if isinstance(parlamentar, Parlamentar):
                        participa = (
                            self.object.emendaloaparlamentar_set.filter(
                                parlamentar=parlamentar, emendaloa__tipo__gt=0
                            ).exists()
                            or self.object.emendaloaparlamentar_set.filter(
                                emendaloa__owner=u, emendaloa__tipo=0
                            ).exists()
                        )

                return (
                    u.has_perm("loa.emendaloa_full_editor") and not self.object.materia
                ) or (
                    u.operadorautor_set.exists()
                    and not self.object.materia
                    and participa
                )

            return has_perm

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

        @property
        def extras_url(self):
            return []
            if (
                self.request.user.is_anonymous
                or not self.request.user.operadorautor_set.exists()
            ):
                return []

            if self.object.fase < EmendaLoa.LIBERACAO_CONTABIL:
                return []

            params = dict(
                descricao=self.object.ementa_format.strip(),
                tipo_materia=(
                    self.object.loa.materia.tipo.id if self.object.loa.materia else ""
                ),
                numero_materia=(
                    self.object.loa.materia.numero if self.object.loa.materia else ""
                ),
                ano_materia=(
                    self.object.loa.materia.ano if self.object.loa.materia else ""
                ),
                tipo=33 if self.object.tipo != EmendaLoa.MODIFICATIVA else 5,
            )

            query_params = urlencode(params)

            return [
                (
                    reverse_lazy("sapl.materia:proposicao_create") + f"?{query_params}",
                    "btn-outline-primary",
                    _("Cadastrar Proposição pré-preenchida"),
                )
            ]

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()

            if "register" in request.GET:
                user = request.user
                if user.is_anonymous:
                    raise PermissionDenied()

                autor_operado = self.request.user.operadorautor_set.values_list(
                    "autor", flat=True
                )
                OperadorAutor = autor_operado.model
                if not OperadorAutor.objects.filter(
                    user=self.object.owner, autor__in=autor_operado
                ).exists():
                    messages.error(
                        request,
                        "Você não tem permissão para registrar a Proposição Legislativa desta Emenda Impositiva/Modificativa.",
                    )
                    return redirect(self.detail_url)

                if self.object.materia:
                    messages.error(
                        request,
                        "A Proposição Legislativa não pode ser gerada novamente pois já foi protocolada e está vinculada a uma Matéria Legislativa.",
                    )
                    return redirect(
                        reverse_lazy(
                            "cmj.loa:emendaloa_detail", kwargs={"pk": self.object.id}
                        )
                    )

                if self.object.fase != EmendaLoa.LIBERACAO_CONTABIL:
                    messages.error(
                        request,
                        'A Proposição Legislativa só pode ser gerada quando a Emenda Impositiva/Modificativa estiver na fase de "Liberado pela Contabilidade e/ou Aguardando Protocolo".',
                    )
                    return redirect(self.detail_url)

                if (
                    self.object.proposicao
                    and self.object.proposicao.data_envio
                    and self.object.proposicao.data_recebimento
                ):
                    messages.warning(
                        request,
                        "A Proposição Legislativa já foi registrada e recebida pelo protocolo, não pode ser atualizada via módulo de Orçamento Impositivo.",
                    )
                    return redirect(
                        reverse_lazy(
                            "sapl.materia:proposicao_detail",
                            kwargs={"pk": self.object.proposicao.id},
                        )
                    )

                if (
                    self.object.proposicao
                    and self.object.proposicao.data_envio
                    and not self.object.proposicao.data_recebimento
                ):
                    messages.warning(
                        request,
                        "A Proposição Legislativa já foi registrada e enviada ao protocolo, para ser atualizada é necessário retomar a proposição antes do protocolo autuar.",
                    )
                    return redirect(
                        reverse_lazy(
                            "sapl.materia:proposicao_detail",
                            kwargs={"pk": self.object.proposicao.id},
                        )
                    )

                try:

                    arq_bytes, arq_name = self.retrieve_file_bytes(request)

                    autor = user.operadorautor_set.first().autor

                    proposicao = self.object.proposicao
                    created = False
                    if not proposicao:
                        np_max = Proposicao.objects.filter(
                            autor=autor,
                            ano=(
                                self.object.loa.materia.ano
                                if self.object.loa.materia
                                else timezone.now().year
                            ),
                        ).aggregate(np=Max("numero_proposicao"))

                        proposicao = Proposicao()
                        proposicao.numero_proposicao = np_max.get("np", 0) + 1
                        created = True
                    else:
                        metadata = proposicao.metadata or {}
                        if (
                            metadata.get("signs", {})
                            .get("texto_original", {})
                            .get("signs", [])
                        ):
                            raise Exception(
                                "Não é possível atualizar a Proposição Legislativa "
                                "de uma Emenda LOA que já foi assinada digitalmente. "
                                "É necessário realizar a substituição manual do arquivo no módulo de Proposições Legislativas."
                            )

                    proposicao.autor = autor

                    proposicao.tipo = TipoProposicao.objects.get(
                        id=33 if self.object.tipo != EmendaLoa.MODIFICATIVA else 5,
                    )
                    proposicao.descricao = self.object.ementa_format
                    proposicao.ano = timezone.now().year
                    proposicao.materia_de_vinculo = self.object.loa.materia
                    proposicao.user = user
                    proposicao.ip = get_client_ip(request)
                    proposicao.texto_original = File(arq_bytes, name=arq_name)
                    proposicao.save()

                    self.object.proposicao = proposicao
                    self.object.save()

                    messages.success(
                        request,
                        f'Proposição Legislativa {"criada" if created else "atualizada"} com sucesso.',
                    )
                    return redirect(
                        reverse_lazy(
                            "sapl.materia:proposicao_detail",
                            kwargs={"pk": proposicao.id},
                        )
                    )
                except Exception as e:
                    messages.error(
                        request,
                        f"Ocorreu um erro ao registrar a Proposição Legislativa: {e}",
                    )

                return redirect(self.detail_url)

            return MasterDetailCrud.DetailView.get(self, request, *args, **kwargs)

        def retrieve_file_bytes(self, request):
            base_url = f"{request.scheme}://{request.get_host()}"

            pra_frente = True
            while True:
                response = requests.get(
                    f"{base_url}/api/loa/emendaloa/{self.object.id}/view/"
                )
                if response.status_code != 200:
                    raise Exception("Não foi possível gerar o PDF da Emenda.")

                arq_name = (
                    response.headers.get(
                        "Content-Disposition", f"emenda_loa_{self.object.id}.pdf"
                    )
                    .split("filename=")[-1]
                    .strip('"')
                )

                arq_bytes = io.BytesIO(response.content)
                pdf = fitz.open(stream=arq_bytes, filetype="pdf")

                if pdf.page_count == 0:
                    break

                if pdf.page_count > 1:
                    pra_frente = False

                md = self.object.metadata
                md["style"] = md.get(
                    "style",
                    {
                        "lineHeight": 150,
                        "espacoAssinatura": 0,
                    },
                )
                md["style"]["espacoAssinatura"] = md["style"].get("espacoAssinatura", 0)
                lineHeight = md["style"]["lineHeight"]

                if lineHeight < 110:
                    break

                if pdf.page_count == 1 and not pra_frente:
                    break

                if pra_frente and lineHeight > 200 and pdf.page_count == 1:
                    break

                if pra_frente:
                    lineHeight += 5
                else:
                    lineHeight -= 1

                md["style"]["lineHeight"] = lineHeight
                self.object.metadata = md
                self.object.save()

                if pra_frente:
                    continue

                page2 = pdf.load_page(1)
                text = page2.get_text("text")
                text = text
                if "A presente emenda fará parte integrante do Projeto" in text:
                    break

            return arq_bytes, arq_name

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
                Arquivo PDF: <a href="{el.materia.texto_original.url}" class="btn btn-link" title="Arquivo PDF da Emenda no Processo Legislativo"><i class="fas fa-file-pdf"></i></a>
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
                pcs.append(
                    f"""<li>
                        <span class="badge badge-secondary">{formats.date_format(pc.prestacao_conta.data_envio, "SHORT_DATE_FORMAT")}</span>
                        <span class="badge badge-secondary">{pc.situacao}</span>
                        <a href="{ pc_url}" class="d-inline-block font-weight-bold pt-1">
                        {pc.prestacao_conta}
                        </a>
                        <span class="text-gray d-block">{pc.detalhamento}</span>
                    </li>"""
                )

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
            # if not self.request.user.is_superuser:
            #    return "", ""
            return verbose_name, field_display, "courier"

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
            for eea in emendaloa.empenhoemendaajuste_set.all():
                empenho = eea.empenho
                url = reverse_lazy("cmj.loa:empenho_detail", kwargs={"pk": empenho.id})
                empenhos.append(
                    f"""
                    <li>
                        <a href="{url}">{empenho.codigo}</a> |
                            Data: {formats.date_format(empenho.data, "SHORT_DATE_FORMAT")} |
                            Valor Empenhado: R$ {empenho.str_valor_empenhado} | {empenho.nome}
                    </li>"""
                )
            return (
                "Empenhos da Emenda",
                f'<ul class="small courier">{"".join(empenhos)}</ul>',
            )
