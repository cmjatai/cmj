from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import (
    Count,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.urls import NoReverseMatch, reverse
from django.utils.datastructures import MultiValueDict

from cmj.loa.services.s_emendaloa import EmendaLoaService

ZERO = Decimal("0.00")
CENTAVO = Decimal("0.01")


def dinheiro(valor):
    """Texto decimal com duas casas, sem formatação regional (LOA-PCC-050)."""
    return str(Decimal(valor or 0).quantize(CENTAVO))


@dataclass
class Selecao:
    """O que uma consulta alcança: os exercícios pedidos e as emendas e os
    registros de ajuste que passam pelos filtros."""

    loas: list
    disponiveis: list
    emendas: object
    ajustes: object
    parlamentar: int = None


@dataclass
class Item:
    """Uma emenda ou um registro de ajuste, com o valor já decidido."""

    classe: str
    id: int
    ano: int
    tipo: int
    fase: int
    valor: Decimal
    valor_original: Decimal
    # valor atribuído a cada parlamentar do item nas distribuições
    partes: dict
    unidade_id: int = None
    entidade_id: int = None
    # "ajuste" ou "impedimento" quando a emenda vale zero por um dos dois
    zerada_por: str = None


class PrestacaoContaService:
    """Consulta consolidada da prestação de contas da LOA
    (docs/specs/loa/prestacao-contas-consulta.md).

    Toda regra de valor, de totalização e de agrupamento fica aqui. As
    consultas recebem o usuário, a LOA da rota e os filtros já validados.
    """

    # LOA-PCC-005: os dois cortes por ano moram aqui, e em nenhum outro lugar
    ANO_INICIAL = 2023
    ANO_INICIAL_EXECUCAO = 2026
    MAX_EXERCICIOS_EXTRAS = 10

    FASE_IMPEDIMENTO = 40
    TIPOS_IMPOSITIVOS = (10, 99)
    TIPO_SAUDE = 10
    TIPO_DIVERSOS = 99
    TIPO_MODIFICATIVA = 0

    # situações em que emendas e ajustes formam um grupo só (LOA-PCC-030)
    SITUACOES_COMUNS = {40: "Impedimento", 60: "Em Execução", 99: "Finalizada"}

    class LoaIndisponivel(Exception):
        """A LOA da rota não tem prestação de contas para este usuário."""

    class PaginaInexistente(Exception):
        pass

    class FiltroInvalido(Exception):
        def __init__(self, erros):
            super().__init__(erros)
            self.erros = erros

    # ------------------------------------------------------------- seleção

    def exercicios_disponiveis(self, user):
        """LOAs com prestação de contas para ``user`` (LOA-PCC-024): as que ele
        vê, com norma, do ano inicial em diante."""
        return (
            EmendaLoaService.loas_visiveis(user)
            .filter(ano__gte=self.ANO_INICIAL, materia__normajuridica__isnull=False)
            .distinct()
            .order_by("-ano")
        )

    def selecionar(self, user, loa, filtros):
        from cmj.api.forms import EmendaLoaFilterSet, RegistroAjusteLoaFilterSet
        from cmj.loa.models import EmendaLoa, RegistroAjusteLoa

        disponiveis = list(self.exercicios_disponiveis(user))
        por_id = {loa_.pk: loa_ for loa_ in disponiveis}
        if loa.pk not in por_id:
            raise self.LoaIndisponivel()

        extras = list(filtros.get("loas") or [])
        if len(extras) > self.MAX_EXERCICIOS_EXTRAS:
            raise self.FiltroInvalido(
                {"loas": [f"No máximo {self.MAX_EXERCICIOS_EXTRAS} exercícios."]}
            )
        if any(pk not in por_id for pk in extras):
            # LOA-PCC-060: sem distinguir inexistente, invisível e sem norma
            raise self.FiltroInvalido({"loas": ["Exercício indisponível."]})
        loas = sorted(
            {por_id[pk] for pk in [loa.pk, *extras]}, key=lambda loa_: -loa_.ano
        )
        ids = [loa_.pk for loa_ in loas]

        # LOA-PCC-002: o que entra depende dos tipos pedidos e de ``ajustes``
        tipos = list(filtros.get("tipos") or [])
        ajustes = bool(filtros.get("ajustes"))
        entram_emendas = bool(tipos) or not ajustes
        entram_ajustes = ajustes or not tipos

        parlamentar = filtros.get("parlamentar")
        comuns = {"situacao": [filtros.get("situacao") or ""]}
        for nome in ("unidade", "entidade", "search"):
            if filtros.get(nome):
                comuns[nome] = [str(filtros[nome])]
        if tipos:
            comuns["tipo__in"] = [",".join(str(t) for t in tipos)]

        emendas = EmendaLoa.objects.none()
        if entram_emendas:
            dados = dict(comuns)
            if parlamentar:
                dados["parlamentares"] = [str(parlamentar)]
            emendas = self._filtrar(
                EmendaLoaFilterSet, EmendaLoa.objects.filter(loa__in=ids), dados
            )

        registros = RegistroAjusteLoa.objects.none()
        if entram_ajustes:
            dados = dict(comuns)
            if parlamentar:
                dados["parlamentares_valor"] = [str(parlamentar)]
            registros = self._filtrar(
                RegistroAjusteLoaFilterSet,
                RegistroAjusteLoa.objects.filter(oficio_ajuste_loa__loa__in=ids),
                dados,
            )

        return Selecao(
            loas=loas,
            disponiveis=disponiveis,
            emendas=emendas,
            ajustes=registros,
            parlamentar=parlamentar,
        )

    # nomes dos filtros nos filtersets -> nome do parâmetro da consulta
    PARAMETRO_DO_FILTRO = {
        "parlamentares": "parlamentar",
        "parlamentares_valor": "parlamentar",
    }

    def _filtrar(self, filterset_class, queryset, dados):
        """LOA-PCC-001: os mesmos filtersets das rotas atuais selecionam os
        registros. Filtro que eles recusam é entrada inválida (LOA-PCC-004)."""
        filterset = filterset_class(data=MultiValueDict(dados), queryset=queryset)
        if not filterset.is_valid():
            raise self.FiltroInvalido(
                {
                    self.PARAMETRO_DO_FILTRO.get(nome, nome): [str(e) for e in erros]
                    for nome, erros in filterset.errors.items()
                }
            )
        return filterset.qs

    # ------------------------------------------------------- valor dos itens

    def _carregar(self, selecao):
        """Os itens da seleção, cada um com o valor decidido (LOA-PCC-010 a
        013). Número fixo de consultas, qualquer que seja a quantidade."""
        from cmj.loa.models import (
            EmendaLoaParlamentar,
            RegistroAjusteLoa,
            RegistroAjusteLoaParlamentar,
        )

        parlamentar = selecao.parlamentar
        ids_emendas = selecao.emendas.order_by().values("pk")
        ids_ajustes = selecao.ajustes.order_by().values("pk")

        emendas = {}
        for e in selecao.emendas.order_by().values(
            "id", "loa__ano", "tipo", "fase", "valor", "unidade_id", "entidade_id"
        ):
            emendas[e["id"]] = e

        com_ajuste = set(
            RegistroAjusteLoa.emendaloa.through.objects.filter(
                emendaloa_id__in=ids_emendas
            ).values_list("emendaloa_id", flat=True)
        )

        partes_emenda = defaultdict(lambda: defaultdict(lambda: ZERO))
        for emenda_id, parlamentar_id, valor in EmendaLoaParlamentar.objects.filter(
            emendaloa_id__in=ids_emendas
        ).values_list("emendaloa_id", "parlamentar_id", "valor"):
            partes_emenda[emenda_id][parlamentar_id] += valor or ZERO

        itens = []
        for e in emendas.values():
            original = e["valor"] or ZERO
            partes = partes_emenda[e["id"]]
            zerada_por = None
            if e["id"] in com_ajuste:
                zerada_por = "ajuste"
            elif e["fase"] == self.FASE_IMPEDIMENTO:
                zerada_por = "impedimento"

            if zerada_por:
                # LOA-PCC-010: o valor remanejado é contado no ajuste
                valor = ZERO
                atribuido = {p: ZERO for p in partes}
            else:
                # LOA-PCC-012: com filtro de parlamentar, a parte dele
                valor = partes.get(parlamentar, original) if parlamentar else original
                atribuido = dict(partes)

            itens.append(
                Item(
                    classe="emenda",
                    id=e["id"],
                    ano=e["loa__ano"],
                    tipo=e["tipo"],
                    fase=e["fase"],
                    valor=valor,
                    valor_original=original,
                    partes=atribuido,
                    unidade_id=e["unidade_id"],
                    entidade_id=e["entidade_id"],
                    zerada_por=zerada_por,
                )
            )

        ajustes = {}
        for a in selecao.ajustes.order_by().values(
            "id",
            "oficio_ajuste_loa__loa__ano",
            "tipo",
            "fase",
            "unidade_id",
            "entidade_id",
        ):
            ajustes[a["id"]] = a

        partes_ajuste = defaultdict(lambda: defaultdict(lambda: ZERO))
        for (
            registro_id,
            parlamentar_id,
            valor,
        ) in RegistroAjusteLoaParlamentar.objects.filter(
            registro_id__in=ids_ajustes
        ).values_list(
            "registro_id", "parlamentar_id", "valor"
        ):
            partes_ajuste[registro_id][parlamentar_id] += valor or ZERO

        for a in ajustes.values():
            partes = partes_ajuste[a["id"]]
            soma, computado = self.valor_do_ajuste(a["fase"], partes.values())
            # LOA-PCC-011: sem valor computado, nenhuma parte vale
            atribuido = {p: (v if computado else ZERO) for p, v in partes.items()}
            valor = atribuido.get(parlamentar, computado) if parlamentar else computado
            itens.append(
                Item(
                    classe="ajuste",
                    id=a["id"],
                    ano=a["oficio_ajuste_loa__loa__ano"],
                    tipo=a["tipo"],
                    fase=a["fase"],
                    valor=valor,
                    valor_original=soma,
                    partes=atribuido,
                    unidade_id=a["unidade_id"],
                    entidade_id=a["entidade_id"],
                )
            )
        return itens

    def valor_do_ajuste(self, fase, partes):
        """LOA-PCC-011: a soma das partes e o valor final, que é zero em
        impedimento."""
        soma = sum((v for v in partes if v), ZERO)
        computado = ZERO if fase == self.FASE_IMPEDIMENTO else soma
        return soma, computado

    def valor_final_da_emenda(self, valor, fase, tem_ajuste):
        """LOA-PCC-010."""
        if tem_ajuste or fase == self.FASE_IMPEDIMENTO:
            return ZERO
        return valor or ZERO

    # --------------------------------------------------------------- resumo

    def resumo(self, user, loa, filtros):
        selecao = self.selecionar(user, loa, filtros)
        itens = self._carregar(selecao)

        def grupo(tipos):
            do_grupo = [i for i in itens if i.tipo in tipos]
            return {
                "valor": dinheiro(sum((i.valor for i in do_grupo), ZERO)),
                "quantidade": len(do_grupo),
            }

        def zeradas(motivo):
            do_motivo = [i for i in itens if i.zerada_por == motivo]
            return {
                "quantidade": len(do_motivo),
                "valor_original": dinheiro(
                    sum((i.valor_original for i in do_motivo), ZERO)
                ),
            }

        selecionadas = {loa_.pk for loa_ in selecao.loas}
        return {
            # LOA-PCC-024
            "exercicios": [
                {
                    "id": loa_.pk,
                    "ano": loa_.ano,
                    "selecionado": loa_.pk in selecionadas,
                }
                for loa_ in selecao.disponiveis
            ],
            # LOA-PCC-020: cada contagem é a do próprio grupo
            "itens": len(itens),
            "emendas": sum(1 for i in itens if i.classe == "emenda"),
            "ajustes": sum(1 for i in itens if i.classe == "ajuste"),
            "impositivas": grupo(self.TIPOS_IMPOSITIVOS),
            "saude": grupo((self.TIPO_SAUDE,)),
            "areas_diversas": grupo((self.TIPO_DIVERSOS,)),
            "modificativas": grupo((self.TIPO_MODIFICATIVA,)),
            # LOA-PCC-023
            "emendas_com_valor_em_ajuste": zeradas("ajuste"),
            "emendas_em_impedimento": zeradas("impedimento"),
            "execucao": self._execucao(selecao),
        }

    def _execucao(self, selecao):
        """LOA-PCC-021: cada empenho ligado a algum item da seleção conta uma
        vez. LOA-PCC-022: diz se os totais valem para os exercícios pedidos."""
        from cmj.loa.models import Empenho, EmpenhoEmendaAjuste

        vinculos = EmpenhoEmendaAjuste.objects.filter(
            Q(emendaloa__in=selecao.emendas.order_by().values("pk"))
            | Q(ajuste__in=selecao.ajustes.order_by().values("pk"))
        ).values("empenho_id")
        totais = Empenho.objects.filter(pk__in=vinculos).aggregate(
            empenhado=Sum("valor_empenhado"),
            liquidado=Sum("valor_liquidado"),
            pago_bruto=Sum("valor_pago_bruto"),
            anulado=Sum("valor_anulado"),
        )
        return {
            "vale": all(loa_.ano >= self.ANO_INICIAL_EXECUCAO for loa_ in selecao.loas),
            "ano_inicial": self.ANO_INICIAL_EXECUCAO,
            **{nome: dinheiro(valor) for nome, valor in totais.items()},
        }

    # ------------------------------------------------------------ dashboard

    def dashboard(self, user, loa, filtros):
        from cmj.loa.models import (
            EmendaLoa,
            Entidade,
            RegistroAjusteLoa,
            UnidadeOrcamentaria,
        )
        from sapl.parlamentares.models import Parlamentar

        selecao = self.selecionar(user, loa, filtros)
        itens = self._carregar(selecao)

        parlamentares = {
            p.pk: p
            for p in Parlamentar.objects.filter(
                pk__in={pk for i in itens for pk in i.partes}
            ).only("id", "nome_parlamentar", "fotografia")
        }
        unidades = {
            u["id"]: u
            for u in UnidadeOrcamentaria.objects.filter(
                pk__in={i.unidade_id for i in itens if i.unidade_id}
            ).values("id", "codigo", "especificacao", "loa__ano")
        }
        entidades = dict(
            Entidade.objects.filter(
                pk__in={i.entidade_id for i in itens if i.entidade_id}
            ).values_list("id", "nome_fantasia")
        )

        def nome_parlamentar(pk):
            return parlamentares[pk].nome_parlamentar

        def unidade(pk):
            u = unidades.get(pk)
            if not u:
                return {"id": None, "nome": None, "ano": None}
            return {
                "id": pk,
                "nome": f"{u['codigo']} - {u['especificacao']}",
                "ano": u["loa__ano"],
            }

        def por_valor(lista):
            return sorted(lista, key=lambda d: (-Decimal(d["valor"]), d["nome"] or ""))

        def por_parlamentar(do_grupo):
            """LOA-PCC-013: o valor de um conjunto de itens por parlamentar."""
            totais = defaultdict(lambda: ZERO)
            for i in do_grupo:
                for pk, valor in i.partes.items():
                    totais[pk] += valor
            return por_valor(
                [
                    {"id": pk, "nome": nome_parlamentar(pk), "valor": dinheiro(v)}
                    for pk, v in totais.items()
                ]
            )

        # LOA-PCC-030: situação por tipo
        rotulos_emenda = dict(EmendaLoa.FASE_CHOICE)
        rotulos_ajuste = dict(RegistroAjusteLoa.FASE_CHOICE)

        def situacao(item):
            if item.fase in self.SITUACOES_COMUNS:
                return f"situacao-{item.fase}", self.SITUACOES_COMUNS[item.fase]
            rotulos = rotulos_emenda if item.classe == "emenda" else rotulos_ajuste
            return (
                f"{item.classe}-{item.fase}",
                str(rotulos.get(item.fase, f"Fase {item.fase}")),
            )

        secoes = []
        for tipo in self.TIPOS_IMPOSITIVOS:
            grupos = {}
            for i in itens:
                if i.tipo != tipo:
                    continue
                chave, rotulo = situacao(i)
                grupos.setdefault(chave, {"rotulo": rotulo, "itens": []})[
                    "itens"
                ].append(i)
            secoes.append(
                {
                    "tipo": tipo,
                    "grupos": sorted(
                        [
                            {
                                "chave": chave,
                                "rotulo": g["rotulo"],
                                "quantidade": len(g["itens"]),
                                "valor": dinheiro(
                                    sum((i.valor for i in g["itens"]), ZERO)
                                ),
                                "parlamentares": por_parlamentar(g["itens"]),
                            }
                            for chave, g in grupos.items()
                        ],
                        key=lambda g: (-g["quantidade"], g["rotulo"]),
                    ),
                }
            )

        diversos = [i for i in itens if i.tipo == self.TIPO_DIVERSOS]

        # LOA-PCC-031: por parlamentar em Áreas Diversas, dividido por unidade
        do_parlamentar = {}
        for i in diversos:
            for pk, valor in i.partes.items():
                p = do_parlamentar.setdefault(
                    pk,
                    {
                        "total": ZERO,
                        "emendas": 0,
                        "ajustes": 0,
                        "unidades": defaultdict(lambda: ZERO),
                    },
                )
                p["total"] += valor
                p["unidades"][i.unidade_id] += valor
                p["emendas" if i.classe == "emenda" else "ajustes"] += 1
        distribuicao_parlamentar = por_valor(
            [
                {
                    "id": pk,
                    "nome": nome_parlamentar(pk),
                    "fotografia": self._fotografia(parlamentares[pk]),
                    "valor": dinheiro(p["total"]),
                    "emendas": p["emendas"],
                    "ajustes": p["ajustes"],
                    "unidades": por_valor(
                        [
                            {**unidade(u), "valor": dinheiro(v)}
                            for u, v in p["unidades"].items()
                        ]
                    ),
                }
                for pk, p in do_parlamentar.items()
            ]
        )

        # LOA-PCC-032 e 033: por unidade e por entidade
        def agrupados(do_grupo, chave, identificacao):
            grupos = defaultdict(list)
            for i in do_grupo:
                if getattr(i, chave):
                    grupos[getattr(i, chave)].append(i)
            return por_valor(
                [
                    {
                        **identificacao(pk),
                        "valor": dinheiro(sum((i.valor for i in g), ZERO)),
                        "quantidade": len(g),
                        "parlamentares": por_parlamentar(g),
                    }
                    for pk, g in grupos.items()
                ]
            )

        emendas_impositivas = [
            i
            for i in itens
            if i.classe == "emenda" and i.tipo in self.TIPOS_IMPOSITIVOS
        ]
        return {
            "situacao": secoes,
            "parlamentares": distribuicao_parlamentar,
            # LOA-PCC-034: as listas saem inteiras; cortar é do painel
            "unidades": agrupados(diversos, "unidade_id", unidade),
            "entidades": agrupados(
                [i for i in emendas_impositivas if entidades.get(i.entidade_id)],
                "entidade_id",
                lambda pk: {"id": pk, "nome": entidades[pk]},
            ),
        }

    # ---------------------------------------------------------------- itens

    def itens(self, user, loa, filtros, page=1, page_size=10):
        """LOA-PCC-040: emendas e depois ajustes, por exercício do mais recente
        para o mais antigo, paginados aqui."""
        from cmj.loa.models import EmendaLoa, RegistroAjusteLoa

        selecao = self.selecionar(user, loa, filtros)

        chaves_emendas = EmendaLoa.objects.filter(
            pk__in=selecao.emendas.order_by().values("pk")
        ).order_by("materia__tipo__sigla", "materia__numero", "pk")
        # pela numeração do registro de ajuste (RAT número/ano)
        chaves_ajustes = RegistroAjusteLoa.objects.filter(
            pk__in=selecao.ajustes.order_by().values("pk")
        ).order_by("ano", "numero", "pk")
        por_ano = defaultdict(lambda: {"emenda": [], "ajuste": []})
        for pk, ano in chaves_emendas.values_list("pk", "loa__ano"):
            por_ano[ano]["emenda"].append(pk)
        for pk, ano in chaves_ajustes.values_list("pk", "oficio_ajuste_loa__loa__ano"):
            por_ano[ano]["ajuste"].append(pk)
        chaves = [
            (classe, pk)
            for ano in sorted(por_ano, reverse=True)
            for classe in ("emenda", "ajuste")
            for pk in por_ano[ano][classe]
        ]

        total = len(chaves)
        paginas = max(1, -(-total // page_size))
        if page > paginas:
            raise self.PaginaInexistente()
        inicio = (page - 1) * page_size
        da_pagina = chaves[inicio : inicio + page_size]

        cartoes = {}
        cartoes.update(
            self._cartoes_de_emenda(
                [pk for classe, pk in da_pagina if classe == "emenda"]
            )
        )
        cartoes.update(
            self._cartoes_de_ajuste(
                [pk for classe, pk in da_pagina if classe == "ajuste"]
            )
        )
        return {
            "pagination": {
                "previous_page": page - 1 if page > 1 else None,
                "next_page": page + 1 if page < paginas else None,
                "start_index": inicio + 1 if da_pagina else 0,
                "end_index": inicio + len(da_pagina),
                "total_entries": total,
                "total_pages": paginas,
                "page": page,
            },
            "results": [cartoes[chave] for chave in da_pagina],
        }

    # --------------------------------------------------------------- opções

    def opcoes(self, user, loa, filtros):
        """LOA-PCC-090: as opções dos seletores de filtro para os exercícios
        pedidos. Dos filtros, só ``loas`` conta."""
        from cmj.loa.models import Entidade, LoaParlamentar, UnidadeOrcamentaria
        from sapl.parlamentares.models import Parlamentar

        selecao = self.selecionar(user, loa, {"loas": filtros.get("loas")})
        ids = [loa_.pk for loa_ in selecao.loas]

        parlamentares = Parlamentar.objects.filter(
            pk__in=LoaParlamentar.objects.filter(loa__in=ids).values("parlamentar_id")
        ).order_by("nome_parlamentar")
        unidades = UnidadeOrcamentaria.objects.filter(
            loa__in=ids, recebe_emenda_impositiva=True
        ).order_by("-loa__ano", "codigo")
        entidades = (
            Entidade.objects.filter(ativo=True)
            .filter(
                Q(emendaloa_set__loa__in=ids)
                | Q(registroajusteloa_set__oficio_ajuste_loa__loa__in=ids)
            )
            .select_related("tipo_entidade")
            .distinct()
            .order_by("nome_fantasia")
        )
        return {
            "parlamentares": [
                {"id": pk, "nome": nome}
                for pk, nome in parlamentares.values_list("pk", "nome_parlamentar")
            ],
            "unidades": [
                {
                    "id": u["id"],
                    "nome": f"{u['codigo']} - {u['especificacao']}",
                    "ano": u["loa__ano"],
                }
                for u in unidades.values("id", "codigo", "especificacao", "loa__ano")
            ],
            # o rótulo é o que o seletor sempre mostrou: o nome e o CNES ou o
            # CNPJ da entidade (LOA-PCL-088)
            "entidades": [
                {"id": e.pk, "nome": e.nome_fantasia, "rotulo": str(e)}
                for e in entidades
            ],
        }

    # ------------------------------------------------------------ relatório

    def relatorio(self, user, loa, filtros):
        """LOA-PCC-070: os itens da seleção com tudo o que o relatório para
        impressão mostra, em número fixo de consultas."""
        selecao = self.selecionar(user, loa, filtros)
        return {
            "loas": selecao.loas,
            "emendas": self._emendas_do_relatorio(selecao),
            "ajustes": self._ajustes_do_relatorio(selecao),
        }

    def _emendas_do_relatorio(self, selecao):
        from cmj.loa.models import (
            DespesaConsulta,
            EmendaLoa,
            EmendaLoaRegistroContabil,
            PrestacaoContaRegistro,
            RegistroAjusteLoa,
        )
        from sapl.materia.models import DocumentoAcessorio, Tramitacao

        unidade_de_tramitacao = ("comissao", "orgao", "parlamentar")
        emendas = list(
            EmendaLoa.objects.filter(pk__in=selecao.emendas.order_by().values("pk"))
            .order_by("-loa__ano", "materia__tipo__sigla", "materia__numero", "pk")
            .select_related(
                "loa",
                "unidade",
                "entidade__tipo_entidade",
                "bairro",
                "materia__tipo",
            )
            .prefetch_related(
                "parlamentares",
                Prefetch(
                    "prestacaocontaregistro_set",
                    queryset=PrestacaoContaRegistro.objects.select_related(
                        "prestacao_conta"
                    ).prefetch_related(
                        "arquivoprestacaocontaregistro_set",
                        "prestacao_conta__arquivoprestacaocontaloa_set",
                    ),
                ),
                "empenhoemendaajuste_set__empenho",
                Prefetch(
                    "registroajusteloa_set",
                    queryset=RegistroAjusteLoa.objects.select_related(
                        "oficio_ajuste_loa", "unidade", "entidade"
                    ).prefetch_related("registroajusteloaparlamentar_set"),
                ),
                Prefetch(
                    "registrocontabil_set",
                    queryset=EmendaLoaRegistroContabil.objects.select_related(
                        "despesa"
                    ),
                ),
                Prefetch(
                    "materia__tramitacao_set",
                    queryset=Tramitacao.objects.select_related(
                        "status",
                        *[
                            f"unidade_tramitacao_local__{r}"
                            for r in unidade_de_tramitacao
                        ],
                        *[
                            f"unidade_tramitacao_destino__{r}"
                            for r in unidade_de_tramitacao
                        ],
                    ),
                ),
                Prefetch(
                    "materia__documentoacessorio_set",
                    queryset=DocumentoAcessorio.objects.select_related("tipo"),
                ),
            )
        )

        # o texto da despesa de cada registro contábil, buscado de uma vez
        ids_despesas = {
            rc.despesa_id
            for e in emendas
            for rc in e.registrocontabil_set.all()
            if rc.despesa_id
        }
        despesas = DespesaConsulta.objects.in_bulk(ids_despesas) if ids_despesas else {}

        for e in emendas:
            tem_ajuste = bool(e.registroajusteloa_set.all())
            # o mesmo que o model responde, sem consulta por emenda
            e.ann_has_ajustes = tem_ajuste
            e.valor_final = self.valor_final_da_emenda(e.valor, e.fase, tem_ajuste)
            e.zerada_por = (
                "ajuste"
                if tem_ajuste
                else ("impedimento" if e.fase == self.FASE_IMPEDIMENTO else None)
            )
            for rc in e.registrocontabil_set.all():
                despesa = despesas.get(rc.despesa_id, rc.despesa)
                rc.texto = f"R$ {rc.str_valor} - {despesa}"
        return emendas

    def _ajustes_do_relatorio(self, selecao):
        from cmj.loa.models import EmendaLoa, PrestacaoContaRegistro, RegistroAjusteLoa

        ajustes = list(
            RegistroAjusteLoa.objects.filter(
                pk__in=selecao.ajustes.order_by().values("pk")
            )
            .order_by("-oficio_ajuste_loa__loa__ano", "ano", "numero", "pk")
            .select_related("oficio_ajuste_loa__loa", "unidade", "entidade")
            .prefetch_related(
                "oficio_ajuste_loa__parlamentares",
                "registroajusteloaparlamentar_set",
                Prefetch(
                    "emendaloa",
                    queryset=EmendaLoa.objects.select_related("materia__tipo"),
                ),
                Prefetch(
                    "prestacaocontaregistro_set",
                    queryset=PrestacaoContaRegistro.objects.select_related(
                        "prestacao_conta"
                    ).prefetch_related(
                        "arquivoprestacaocontaregistro_set",
                        "prestacao_conta__arquivoprestacaocontaloa_set",
                    ),
                ),
                "empenhoemendaajuste_set__empenho",
            )
        )
        for a in ajustes:
            _, a.valor_final = self.valor_do_ajuste(
                a.fase, [p.valor for p in a.registroajusteloaparlamentar_set.all()]
            )
        return ajustes

    @staticmethod
    def _contagem(queryset):
        """Subconsulta que conta as linhas de ``queryset``, já filtrado pela
        linha de fora."""
        return Coalesce(
            Subquery(
                queryset.order_by()
                .annotate(_um=Value(1))
                .values("_um")
                .annotate(total=Count("pk", distinct=True))
                .values("total"),
                output_field=IntegerField(),
            ),
            0,
        )

    @staticmethod
    def _fotografia(parlamentar):
        return parlamentar.fotografia.url if parlamentar.fotografia else None

    @staticmethod
    def _link(nome, pk):
        try:
            return reverse(f"cmj.loa:{nome}_detail", kwargs={"pk": pk})
        except NoReverseMatch:
            return ""

    def _parlamentares_do_cartao(self, partes):
        """Parlamentares de um cartão, com a parte de cada um, por nome."""
        por_id = {}
        for parte in partes:
            p = parte.parlamentar
            atual = por_id.setdefault(p.pk, {"parlamentar": p, "valor": ZERO})
            atual["valor"] += parte.valor or ZERO
        return [
            {
                "id": pk,
                "nome": d["parlamentar"].nome_parlamentar,
                "fotografia": self._fotografia(d["parlamentar"]),
                "valor": dinheiro(d["valor"]),
            }
            for pk, d in sorted(
                por_id.items(), key=lambda kv: kv[1]["parlamentar"].nome_parlamentar
            )
        ]

    @staticmethod
    def _unidade_do_cartao(unidade):
        if not unidade:
            return None
        return {"id": unidade.pk, "nome": f"{unidade.codigo} - {unidade.especificacao}"}

    @staticmethod
    def _entidade_do_cartao(entidade):
        if not entidade:
            return None
        return {"id": entidade.pk, "nome": entidade.nome_fantasia}

    @staticmethod
    def titulo_da_emenda(emenda):
        """A epígrafe da matéria ou, sem matéria, o valor (LOA-PCL-046)."""
        if emenda.materia_id:
            return emenda.materia.epigrafe_short
        return emenda.str_short.strip()

    def _cartoes_de_emenda(self, ids):
        """LOA-PCC-041 e 043, para emendas."""
        from cmj.loa.models import (
            EmendaLoa,
            EmendaLoaParlamentar,
            EmpenhoEmendaAjuste,
            PrestacaoContaRegistro,
            RegistroAjusteLoa,
        )
        from sapl.materia.models import DocumentoAcessorio, Tramitacao

        if not ids:
            return {}
        vinculos = RegistroAjusteLoa.emendaloa.through.objects
        emendas = (
            EmendaLoa.objects.filter(pk__in=ids)
            .select_related(
                "loa",
                "unidade",
                "entidade__tipo_entidade",
                "bairro",
                "materia__tipo",
            )
            .prefetch_related(
                Prefetch(
                    "emendaloaparlamentar_set",
                    queryset=EmendaLoaParlamentar.objects.select_related("parlamentar"),
                )
            )
            .annotate(
                n_ajustes=self._contagem(vinculos.filter(emendaloa_id=OuterRef("pk"))),
                n_prestacao=self._contagem(
                    PrestacaoContaRegistro.objects.filter(emendaloa=OuterRef("pk"))
                ),
                # os vínculos de empenho da emenda e os dos ajustes dela
                n_empenhos=self._contagem(
                    EmpenhoEmendaAjuste.objects.filter(
                        Q(emendaloa=OuterRef("pk"))
                        | Q(ajuste__emendaloa=OuterRef("pk"))
                    )
                ),
                n_tramitacoes=self._contagem(
                    Tramitacao.objects.filter(materia=OuterRef("materia"))
                ),
                n_documentos=self._contagem(
                    DocumentoAcessorio.objects.filter(materia=OuterRef("materia"))
                ),
            )
        )
        rotulos_tipo = dict(EmendaLoa.TIPOEMENDALOA_CHOICE)
        rotulos_fase = dict(EmendaLoa.FASE_CHOICE)
        cartoes = {}
        for e in emendas:
            tem_ajustes = e.n_ajustes > 0
            cartoes[("emenda", e.pk)] = {
                "classe": "emenda",
                "id": e.pk,
                "loa": {"id": e.loa_id, "ano": e.loa.ano},
                "titulo": self.titulo_da_emenda(e),
                "link": self._link("emendaloa", e.pk),
                "tipo": e.tipo,
                "tipo_rotulo": str(rotulos_tipo.get(e.tipo, "")),
                "fase": e.fase,
                # LOA-PCC-042
                "fase_rotulo": str(rotulos_fase.get(e.fase, "")),
                "valor_original": dinheiro(e.valor),
                "valor_final": dinheiro(
                    self.valor_final_da_emenda(e.valor, e.fase, tem_ajustes)
                ),
                "tem_ajustes": tem_ajustes,
                "parlamentares": self._parlamentares_do_cartao(
                    e.emendaloaparlamentar_set.all()
                ),
                "unidade": self._unidade_do_cartao(e.unidade),
                "entidade": self._entidade_do_cartao(e.entidade),
                "objeto": e.ementa_format,
                "materia": e.materia_id,
                "abas": {
                    "prestacao": e.n_prestacao,
                    "ajustes": e.n_ajustes,
                    "empenhos": e.n_empenhos,
                    "tramitacoes": e.n_tramitacoes if e.materia_id else 0,
                    "documentos": e.n_documentos if e.materia_id else 0,
                },
            }
        return cartoes

    def _cartoes_de_ajuste(self, ids):
        """LOA-PCC-041 e 043, para registros de ajuste."""
        from cmj.loa.models import (
            EmendaLoa,
            EmpenhoEmendaAjuste,
            PrestacaoContaRegistro,
            RegistroAjusteLoa,
            RegistroAjusteLoaParlamentar,
        )

        if not ids:
            return {}
        ajustes = (
            RegistroAjusteLoa.objects.filter(pk__in=ids)
            .select_related("oficio_ajuste_loa__loa", "unidade", "entidade")
            .prefetch_related(
                Prefetch(
                    "registroajusteloaparlamentar_set",
                    queryset=RegistroAjusteLoaParlamentar.objects.select_related(
                        "parlamentar"
                    ),
                ),
                Prefetch(
                    "emendaloa",
                    queryset=EmendaLoa.objects.select_related("materia__tipo").order_by(
                        "pk"
                    ),
                ),
            )
            .annotate(
                n_prestacao=self._contagem(
                    PrestacaoContaRegistro.objects.filter(
                        registro_ajuste=OuterRef("pk")
                    )
                ),
                n_empenhos=self._contagem(
                    EmpenhoEmendaAjuste.objects.filter(ajuste=OuterRef("pk"))
                ),
            )
        )
        rotulos_tipo = dict(RegistroAjusteLoa.TIPOEMENDALOA_CHOICE)
        rotulos_fase = dict(RegistroAjusteLoa.FASE_CHOICE)
        cartoes = {}
        for a in ajustes:
            partes = list(a.registroajusteloaparlamentar_set.all())
            soma, computado = self.valor_do_ajuste(a.fase, [p.valor for p in partes])
            loa = a.oficio_ajuste_loa.loa
            cartoes[("ajuste", a.pk)] = {
                "classe": "ajuste",
                "id": a.pk,
                "loa": {"id": loa.pk, "ano": loa.ano},
                "titulo": str(a),
                "link": self._link("registroajusteloa", a.pk),
                "tipo": a.tipo,
                "tipo_rotulo": str(rotulos_tipo.get(a.tipo, "")),
                "fase": a.fase,
                "fase_rotulo": str(rotulos_fase.get(a.fase, "")),
                "valor": dinheiro(soma),
                "valor_final": dinheiro(computado),
                "parlamentares": self._parlamentares_do_cartao(partes),
                "unidade": self._unidade_do_cartao(a.unidade),
                "entidade": self._entidade_do_cartao(a.entidade),
                "emendas": [
                    {"id": e.pk, "titulo": self.titulo_da_emenda(e)}
                    for e in a.emendaloa.all()
                ],
                "descricao": a.descricao,
                "abas": {
                    "prestacao": a.n_prestacao,
                    "empenhos": a.n_empenhos,
                },
            }
        return cartoes
