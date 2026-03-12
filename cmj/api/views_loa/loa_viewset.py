import logging
from decimal import Decimal

from _collections import OrderedDict
from django.db.models import F
from django.db.models.aggregates import Sum
from django.db.models.expressions import Func, OuterRef, Subquery
from django.db.models.functions import Substr
from django.db.models.functions.comparison import Coalesce
from django.utils import formats
from django.utils.datastructures import OrderedSet
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from rest_framework.response import Response

from cmj.loa.models import (
    Acao,
    Despesa,
    EmendaLoaRegistroContabil,
    Fonte,
    Funcao,
    Natureza,
    Orgao,
    Programa,
    SubFuncao,
    UnidadeOrcamentaria,
)
from cmj.utils import TimeExecution, decimal2str, run_sql
from sapl.api.permissions import SaplModelPermissions

logger = logging.getLogger(__name__)

filters_base = [
    ("orgao", Orgao),
    ("unidade", UnidadeOrcamentaria),
    ("funcao", Funcao),
    ("subfuncao", SubFuncao),
    ("programa", Programa),
    ("acao", Acao),
    ("natureza_1", Natureza),
    ("natureza_2", Natureza),
    ("natureza_3", Natureza),
    ("natureza_4", Natureza),
    ("natureza_5", Natureza),
    ("fonte", Fonte),
]
dict_filter_base = dict(filters_base)


class LoaViewSet:

    class LoaPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            has_perm = super().has_permission(request, view)

            if has_perm:
                return has_perm

            u = request.user

            if request.method == "POST" and view.action in (
                "despesas_agrupadas",
                "espelho",
            ):
                return True

            if request.method == "GET" and view.action in ("retrieve",):
                self.object = view.get_object()
                if not self.object.publicado and u.is_anonymous:
                    return False
                return True
            elif request.method == "GET" and view.action == "despesas_executadas":
                return u.has_perm("loa.view_despesasexecutadas")
            return False

    permission_classes = (LoaPermission,)

    @action(
        methods=[
            "get",
        ],
        detail=True,
    )
    def despesas_executadas(self, request, *args, **kwargs):
        ano = kwargs["pk"]
        result = run_sql(
            f"""SELECT
                q1.cod as orgao,
                q1.especificacao,
                q1.valor as val_orc,
                q2.valor as val_exe,
                q3.valor as val_rec_orc,
                to_char(q2.data_max, 'DD/MM/YYYY') as data_max,
                q2.codigo_max

            FROM (
                SELECT
                    lo.codigo as cod,
                    lo.especificacao as especificacao,
                    SUM(ldo.valor_materia) as valor
                FROM loa_orgao lo
                    LEFT JOIN loa_despesa ldo ON (ldo.orgao_id = lo.id)
                    INNER JOIN loa_loa ll ON (lo.loa_id = ll.id)
                WHERE ll.ano = {ano}
                    group by cod, especificacao
                    ORDER BY cod, especificacao
                ) q1
                LEFT JOIN (
                    SELECT
                        lo.codigo as cod,
                        lo.especificacao as especificacao,
                        SUM(ldp.valor) as valor,
                        MAX(ldp.data) as data_max,
                        MAX(ldp.codigo) as codigo_max
                    FROM loa_orgao lo
                        LEFT JOIN loa_despesapaga ldp ON (ldp.orgao_id = lo.id)
                        INNER JOIN loa_loa ll ON (lo.loa_id = ll.id)
                    WHERE ll.ano = {ano}
                        group by cod, especificacao
                        ORDER BY cod, especificacao
                ) q2 on (q1.cod = q2.cod)
                LEFT JOIN (
                    SELECT
                        lo.codigo as cod,
                        lo.especificacao as especificacao,
                        SUM(
                            CASE WHEN lro.codigo like '9%' then -lra.valor else lra.valor end
                            ) as valor
                    FROM loa_orgao lo
                        LEFT JOIN loa_receitaorcamentaria lro ON (lro.orgao_id = lo.id)
                        LEFT JOIN loa_receitaarrecadada lra ON (lra.receita_id = lro.id)
                        INNER JOIN loa_loa ll ON (lo.loa_id = ll.id)
                    WHERE ll.ano = {ano}
                        group by cod, especificacao
                        ORDER BY cod, especificacao
                ) q3 on (q1.cod = q3.cod)
                order by q2.valor desc nulls last;
        """
        )

        return Response(result)

    @action(
        methods=[
            "post",
        ],
        detail=True,
    )
    def despesas_agrupadas(self, request, *args, **kwargs):
        loa_id = kwargs["pk"]

        filters_data = request.data

        try:
            itens = filters_data.pop("itens")
            if itens != 1000:
                itens = min(25, int(itens))

            hist = filters_data.pop("hist")
            hist = int(hist)
        except:
            itens = 20
            hist = 0

        grup_str = filters_data.pop("agrupamento")
        agrup = {}

        if "natureza" not in grup_str:
            agrup["codigo"] = F(f"{grup_str}__codigo")
            # agrup['especificacao'] = F(f'{grup_str}__especificacao')
            order_by = [f"{grup_str}__codigo"]

            if grup_str == "unidade":
                agrup["orgao__codigo"] = F("orgao__codigo")
                order_by.insert(0, "orgao__codigo")
                pass
        else:
            ndict = {1: 1, 2: 3, 3: 6, 4: 9, 5: 12}
            nivel = int(grup_str.split("_")[1])

            agrup["codigo"] = Substr(f"natureza__codigo", 1, ndict[nivel])
            order_by = ["natureza__codigo"]

        agrup["ano"] = F("loa__ano")
        order_by.insert(0, "-loa__ano")

        f_unidade = filters_data.get("unidade", None)
        if f_unidade:
            ucod = f_unidade.split("/")
            filters_data["unidade"] = ucod[0]

        filters = {
            f"{k}__codigo": v
            for k, v in filters_data.items()
            if v and k in dict_filter_base
        }
        filters["loa_id"] = loa_id

        if f_unidade:
            filters["unidade__orgao_id"] = ucod[1]

        if hist:
            filters.pop("loa_id")

        if "natureza" not in grup_str:
            filter_sum_rc = {f"despesa__{grup_str}": OuterRef(grup_str)}
        else:
            filter_sum_rc = {f"despesa__natureza": OuterRef("natureza")}

        sum_registros = (
            EmendaLoaRegistroContabil.objects.filter(**filter_sum_rc)
            .annotate(sum_registros=Coalesce(Func("valor", function="Sum"), Decimal(0)))
            .values("sum_registros")
        )
        sum_registros.query.clear_ordering()

        rs = (
            Despesa.objects.filter(**filters)
            .values(**agrup)
            .order_by(*order_by)
            .annotate(
                vm=Sum("valor_materia"),
                vn=Sum("valor_norma"),
                alt=Subquery(sum_registros),
            )
        )
        rs = list(rs)

        r = []
        r_anual = OrderedDict()
        labels = {}
        for i in rs:
            ano = i["ano"]
            if ano not in r_anual:
                r_anual[ano] = []

            i.pop("ano")
            try:
                codigo_unico = f'{i["codigo"]}/{i["orgao__codigo"] if "orgao__codigo" in i else ""}'
                if codigo_unico not in labels:
                    params = {
                        "loa__ano": ano,
                        f'codigo{"__startswith" if "natureza" in grup_str else ""}': i[
                            "codigo"
                        ],
                    }
                    if "orgao__codigo" in i:
                        params["orgao__codigo"] = i["orgao__codigo"]

                    i["especificacao"] = (
                        dict_filter_base[grup_str]
                        .objects.filter(**params)
                        .values_list("especificacao", flat=True)
                        .first()
                    )
                    labels[codigo_unico] = i["especificacao"]
                else:
                    i["especificacao"] = labels[i["codigo"]]

            except:
                i["especificacao"] = ""
            r_anual[ano].append(i)

        for ano, rs in r_anual.items():

            if "natureza" not in grup_str:
                r = rs
            else:
                r = {}
                for i in rs:
                    nat = i["codigo"]
                    if nat not in r:
                        r[nat] = i
                        r[nat]["vm"] = i["vm"] or Decimal("0.00")
                        r[nat]["vn"] = i["vn"] or Decimal("0.00")
                        r[nat]["alt"] = i["alt"] or Decimal("0.00")
                        continue

                    r[nat]["vm"] += i["vm"] or Decimal("0.00")
                    r[nat]["vn"] += i["vn"] or Decimal("0.00")
                    r[nat]["alt"] += i["alt"] or Decimal("0.00")
                r = r.values()

                for i in r:
                    cod = i["codigo"]
                    cod = cod.split(".")
                    while len(cod) < 5:
                        cod.append("0" * 2 if len(cod) > 1 else "0")
                    cod = ".".join(cod)
                    nat = Natureza.objects.filter(loa_id=loa_id, codigo=cod).first()
                    i["especificacao"] = nat.especificacao if nat else ""

            soma = sum(map(lambda x: x["vm"], r))

            r = sorted(r, key=lambda x: -x["vm"])

            if not hist:
                outros = r[itens:] if itens else []
                r = r[:itens] if itens else r

                if outros:
                    outros[0]["vm"] = outros[0]["vm"] or Decimal("0.00")
                    outros[0]["vn"] = outros[0]["vn"] or Decimal("0.00")
                    outros[0]["alt"] = outros[0]["alt"] or Decimal("0.00")

                    for idx, item in enumerate(outros):
                        if idx:
                            outros[0]["vm"] += item["vm"] or Decimal("0.00")
                            outros[0]["vn"] += item["vn"] or Decimal("0.00")
                            outros[0]["alt"] += item["alt"] or Decimal("0.00")

                    outros[0]["codigo"] = " " * len(outros[0]["codigo"])
                    outros[0]["especificacao"] = "OUTROS"
                    r.append(outros[0])

                for idx, item in enumerate(r):
                    esp = item["especificacao"]
                    item["especificacao"] = f"{esp}"
                    r[idx]["vp"] = int((item["vm"] / soma) * 100)
                    r[idx]["vm_soma"] = formats.number_format(soma, force_grouping=True)

                    vm = formats.number_format(item["vm"], force_grouping=True)
                    while len(vm) < 14:
                        vm = f" {vm}"
                    r[idx]["vm_str"] = vm

                    a = formats.number_format(item["alt"], force_grouping=True)
                    while len(a) < 14:
                        a = f" {a}"
                    r[idx]["alt_str"] = a

                    r[idx]["saldo"] = item["vm"] + item["alt"]
                    s = formats.number_format(r[idx]["saldo"], force_grouping=True)
                    while len(s) < 14:
                        s = f" {s}"
                    r[idx]["saldo_str"] = s

            r_anual[ano] = r

        if hist:
            os_esp = OrderedSet()
            new_r_anual = {}

            for ano, items in r_anual.items():
                new_r_anual[ano] = []
                codigos = map(
                    lambda i: f'{i["codigo"]}/{i["orgao__codigo"] if "orgao__codigo" in i else ""}',
                    items,
                )
                for cod in codigos:
                    os_esp.add(cod)
            # os_esp = os_esp - {'  '}
            # os_esp = os_esp.union(['  '])
            len_osesp = len(os_esp)

            ks_esp = dict(zip(os_esp, range(len_osesp)))

            for ano in r_anual.keys():
                new_r_anual[ano] = [{}] * len_osesp

            for ano, items in r_anual.items():
                for item in items:
                    codigo_unico = f'{item["codigo"]}/{item["orgao__codigo"] if "orgao__codigo" in item else ""}'
                    new_r_anual[ano][ks_esp[codigo_unico]] = item
            anos = list(new_r_anual.keys())
            anos.reverse()
            labels = [f'{c.split("/")[0]}-{labels[c]}' for c in list(os_esp)]
            r_anual = {"labels": labels, "anos": anos, "pre_datasets": new_r_anual}

        r_anual = dict(r_anual)

        return Response(r_anual if hist else r)

    @action(
        methods=[
            "post",
        ],
        detail=True,
    )
    def espelho(self, request, *args, **kwargs):
        loa = self.get_object()
        filters_data = request.data
        return Response(self.run_espelho(filters_data, loa))

    def run_espelho(self, filters_data, loa):

        try:
            itens = filters_data.pop("itens")
            if itens != 1000:
                itens = min(25, int(itens))

            hist = filters_data.pop("hist")
            hist = int(hist)
        except:
            itens = 20
            hist = 0

        filter_sql = []
        field_to_alias = {
            "orgao": "o",
            "unidade": "u",
            "funcao": "f",
            "subfuncao": "sf",
            "programa": "p",
            "acao": "a",
            "natureza_1": "n",
            "natureza_2": "n",
            "natureza_3": "n",
            "natureza_4": "n",
            "natureza_5": "n",
            "fonte": "fte",
        }
        for k, v in filters_data.items():
            if v and k in field_to_alias:
                if "/" in v:
                    v = v.split("/")
                    filter_sql.append(
                        f" {field_to_alias[k]}.codigo = '{v[0]}' and {field_to_alias[k]}.orgao_id = {v[1]} "
                    )
                else:
                    filter_sql.append(f" {field_to_alias[k]}.codigo = '{v}' ")
        filter_sql = " and ".join(filter_sql)
        filter_sql = f" and {filter_sql} " if filter_sql else ""

        # TODO: refatorar "sql" para usar o modelo de dados de view db não gerenciada pelo django
        sql_geral = f"""SELECT distinct
                            d.id,
                            d.valor_materia,
                            loa.ano || '.' || o.codigo || '.' || u.codigo || '.' || f.codigo || '.' || sf.codigo || '.' || p.codigo || '.' || a.codigo || '.' || n.codigo || '.' || fte.codigo as codigo,
                            loa.ano || o.codigo || u.codigo || f.codigo || sf.codigo || p.codigo || a.codigo || n.codigo || fte.codigo as codigo_base,
                            SUM(CASE WHEN elrc.valor > 0 THEN elrc.valor ELSE 0 END) OVER (PARTITION BY d.id) AS soma_registroscontabeis_acrescimo,
                            SUM(CASE WHEN elrc.valor < 0 THEN elrc.valor ELSE 0 END) OVER (PARTITION BY d.id) AS soma_registroscontabeis_reducao

                        from loa_despesa d
                            inner join loa_loa             loa on (loa.id = d.loa_id)
                            inner join loa_orgao             o on (  o.id = d.orgao_id)
                            inner join loa_unidadeorcamentaria           u on (  u.id = d.unidade_id)
                            inner join loa_funcao            f on (  f.id = d.funcao_id)
                            inner join loa_subfuncao        sf on ( sf.id = d.subfuncao_id)
                            inner join loa_programa          p on (  p.id = d.programa_id)
                            inner join loa_acao              a on (  a.id = d.acao_id)
                            inner join loa_natureza          n on (  n.id = d.natureza_id)
                            inner join loa_fonte           fte on (fte.id = d.fonte_id)
                            left outer join loa_emendaloaregistrocontabil elrc on (elrc.despesa_id = d.id)
                            where loa.id = {loa.pk} {filter_sql} order by codigo_base
        """

        mask_union = """
            (
                SELECT DISTINCT
                    Substr(codigo_base, 1, {partcb}) AS codigo_base, Substr(codigo, 1, {partc}) AS codigo,
                    SUM(valor_materia) AS soma,
                    SUM(soma_registroscontabeis_acrescimo) AS soma_registroscontabeis_acrescimo,
                    SUM(soma_registroscontabeis_reducao) AS soma_registroscontabeis_reducao
                    FROM (
                        {sql_geral}
                    ) todas_as_despesas
                        GROUP BY
                            Substr(codigo_base, 1, {partcb}), Substr(codigo, 1, {partc})
                            /* HAVING SUM(valor_materia) > 0*/
                        order by codigo_base
            )
        """

        # TODO: refatorar mask para montar o case com laço
        # mask_codigo = '1234.67.90.23.567.9012.4.678.0.2.45.78.01.345'
        # mask_codbas = '1234 56 78 90 123 4567 89012 345678901234 567'
        parts_codigo = [4, 7, 10, 13, 17, 22, 28, 41, 45]
        parts_codigo_base = [4, 6, 8, 10, 13, 17, 22, 34, 37]

        agrupamento_select = filters_data.pop("agrupamento", "fonte")
        agrupamentos = dict(
            [
                ("orgao", 7),
                ("unidade", 10),
                ("funcao", 13),
                ("subfuncao", 17),
                ("programa", 22),
                ("acao", 28),
                ("natureza_1", 30),
                ("natureza_2", 32),
                ("natureza_3", 35),
                ("natureza_4", 38),
                ("natureza_5", 41),
                ("fonte", 45),
            ]
        )
        agrupamentos_inverse = {v: k for k, v in agrupamentos.items()}

        columns = [
            "geral.codigo",
            "geral.codigo_base",
            "geral.soma",
            f"""
                CASE
                    when LENGTH(codigo_base) = 6  then (select especificacao                   from loa_orgao                       where loa_orgao.codigo             = substr(codigo_base, 5, 2) limit 1)

                    when LENGTH(codigo_base) = 8  then (select loa_unidadeorcamentaria.especificacao from loa_unidadeorcamentaria
                                                            inner join loa_orgao on loa_orgao.id = loa_unidadeorcamentaria.orgao_id where loa_unidadeorcamentaria.codigo = substr(codigo_base, 7, 2) and loa_orgao.codigo = substr(codigo_base, 5, 2) limit 1)

                    when LENGTH(codigo_base) = 10 then (select especificacao from loa_funcao    where loa_funcao.codigo    = substr(codigo_base, 9, 2) limit 1)
                    when LENGTH(codigo_base) = 13 then (select especificacao from loa_subfuncao where loa_subfuncao.codigo = substr(codigo_base, 11, 3) limit 1)
                    when LENGTH(codigo_base) = 17 then (select especificacao from loa_programa  where loa_programa.codigo  = substr(codigo_base, 14, 4) limit 1)
                    when LENGTH(codigo_base) = 22 then (select especificacao from loa_acao      where loa_acao.codigo      = substr(codigo_base, 18, 5) limit 1)
                    when LENGTH(codigo_base) = 34 then (select especificacao from loa_natureza  where loa_natureza.codigo  = substr(codigo_base, 23, 12) limit 1)
                    when LENGTH(codigo_base) = 37 then (select especificacao from loa_fonte     where loa_fonte.codigo     = substr(codigo_base, 35, 3) limit 1)
                        else ''
                END as especificacao
            """,
            "geral.soma_registroscontabeis_acrescimo",
            "geral.soma_registroscontabeis_reducao",
        ]

        sql_for_run = f"""
            select
                {', '.join(columns)}
                from (
                    {
            'union '.join(
                [
                    mask_union.format(
                        partc=partc, partcb=partcb, sql_geral=sql_geral
                    )
                    for partc, partcb in zip(parts_codigo, parts_codigo_base)
                ]
            )
        }) geral order by codigo_base
            """

        with TimeExecution():  #'gerar_espelho'
            # print('Running SQL for espelho:', sql_for_run)
            results = run_sql(sql_for_run)

        rs = []
        lr_old = 0
        value = Decimal(0)

        # parts_codigo =      [4, 7, 10, 13, 17, 22, 28, 41, 46]
        # parts_codigo_base = [4, 6,  8, 10, 13, 17, 22, 34, 37]

        if agrupamento_select in (
            "natureza_1",
            "natureza_2",
            "natureza_3",
            "natureza_4",
            "natureza_5",
        ):
            agrupamento_select = "natureza_5"

        agrupamento = agrupamentos.get(agrupamento_select, 45)
        agrupamento_local = agrupamento
        for i, rr in enumerate(results):
            lr = len(rr[0])
            # remove natureza da despesa do tipo X.X.XX.XX.00 se este for igual a X.X.XX.XX
            if lr == 41 and rr[1][-2:] == "00":
                if rr[2:6] == results[i - 1][2:6]:
                    continue

            r = list(rr)
            r[2] = r[2] or Decimal(0)  # valor_materia

            acrescimo = r[4] or Decimal(0)
            reducao = r[5] or Decimal(0)
            ar = acrescimo + reducao

            if lr < lr_old:
                agrupamento_local = agrupamento

            if (acrescimo or reducao) and ar == Decimal(0) and lr == agrupamento_local:
                idx_part = parts_codigo.index(lr)
                agrupamento_local = (
                    parts_codigo[idx_part + 1]
                    if idx_part + 1 < len(parts_codigo)
                    else 45
                )

            if lr > agrupamento_local:
                continue

            saldo = r[2] + ar

            r.append(ar)  # acrescimo + reducao
            r.append(saldo)  # saldo
            r.append(lr == agrupamento_local)
            rs.append(r)

            d2s = decimal2str(r[2])
            dAcrescimo2s = decimal2str(acrescimo) if acrescimo else ""
            dReducao2s = decimal2str(reducao) if reducao else ""
            dAr2s = decimal2str(ar) if ar else ""
            dSaldo2s = decimal2str(saldo) if saldo else ""
            # old code substituido a partir daqui

            r[2] = d2s
            r[4] = dAcrescimo2s
            r[5] = dReducao2s
            r[6] = dAr2s
            r[7] = dSaldo2s

            lr_old = lr

            r[0] = r[0][5:]
            r[3] = r[3] or ""

            if len(r[0]) > 36:
                r[0] = f'{"&nbsp;" * 20}{r[0][37:]}'
            elif len(r[0]) > 23:
                r[0] = f'{"&nbsp;" * 8}..{r[0][23:]}'  # 22 space - original
            else:
                # r[0] = f'{r[0]}<div class="ident">{"&nbsp;" * (min(28, agrupamento) - len(r[0]) - 5)}</div>'
                r[0] = f'{r[0]}{" " * (min(28, agrupamento_local) - len(r[0]) - 5)}'
                # print(r[0])
                pass

        return rs
