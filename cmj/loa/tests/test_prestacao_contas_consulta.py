"""Consulta consolidada da prestação de contas da LOA
(docs/specs/loa/prestacao-contas-consulta.md)."""

import datetime
from decimal import Decimal
from unittest import mock
from urllib.parse import urlencode

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from model_bakery import baker as mommy
from rest_framework.test import APIClient

import sapl.api.urls  # noqa: F401  (registra os viewsets)
from cmj.loa.models import (
    EmendaLoa,
    EmendaLoaParlamentar,
    Empenho,
    EmpenhoEmendaAjuste,
    Entidade,
    Loa,
    OficioAjusteLoa,
    Orgao,
    RegistroAjusteLoa,
    RegistroAjusteLoaParlamentar,
    UnidadeOrcamentaria,
)
from cmj.loa.services.s_prestacaoconta import PrestacaoContaService
from cmj.mixins import GoogleRecapthaViewMixin
from sapl.materia.models import MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Legislatura

pytestmark = [pytest.mark.django_db]

servico = PrestacaoContaService()
ANONIMO = AnonymousUser()


# ---------------------------------------------------------------- cenário


@pytest.fixture(autouse=True)
def legislatura_atual(db):
    return Legislatura.objects.create(
        numero=99,
        data_inicio=datetime.date(2025, 1, 1),
        data_fim=datetime.date(2028, 12, 31),
        data_eleicao=datetime.date(2024, 10, 6),
    )


def _loa(ano, publicado=True, com_norma=True):
    materia = mommy.make(
        MateriaLegislativa,
        numero=ano,
        ano=ano - 1,
        data_apresentacao=datetime.date(ano - 1, 9, 1),
        em_tramitacao=False,
    )
    if com_norma:
        mommy.make(NormaJuridica, materia=materia)
    return mommy.make(Loa, ano=ano, publicado=publicado, materia=materia)


@pytest.fixture
def loa(legislatura_atual):
    """LOA publicada e com norma: a prestação de contas só vale para ela."""
    return _loa(2027)


def _ajuste(loa, numero, tipo, fase, partes, emendas=(), unidade=None):
    oficio = mommy.make(OficioAjusteLoa, loa=loa)
    # o hook de busca do ajuste lê o M2M antes de haver pk
    ajuste = mommy.prepare(
        RegistroAjusteLoa,
        numero=numero,
        ano=loa.ano,
        tipo=tipo,
        fase=fase,
        oficio_ajuste_loa=oficio,
        unidade=unidade,
        entidade=None,
        descricao=f"Ajuste {numero}",
    )
    ajuste.save(auto_update_search=False)
    ajuste.emendaloa.add(*emendas)
    for parlamentar, valor in partes:
        RegistroAjusteLoaParlamentar.objects.create(
            registro=ajuste, parlamentar=parlamentar, valor=Decimal(valor)
        )
    return ajuste


def _empenho(loa, empenhado, liquidado, pago, anulado):
    orgao = Orgao.objects.filter(loa=loa).first() or mommy.make(
        Orgao, loa=loa, codigo="01"
    )
    return mommy.make(
        Empenho,
        orgao=orgao,
        valor_empenhado=Decimal(empenhado),
        valor_liquidado=Decimal(liquidado),
        valor_pago_bruto=Decimal(pago),
        valor_anulado=Decimal(anulado),
        _fill_optional=False,
    )


@pytest.fixture
def cenario(loa, unidade, parlamentar, parlamentar_b, make_emenda):
    """O emaranhado em miniatura.

    e1  diversos, aprovada, 1000 (A), com entidade e empenho
    e2  saúde, em execução, 600 (A 400, B 200)
    e3  diversos, aprovada, 500 (A), com os ajustes aj1 e aj2 -> vale zero
    e4  diversos, impedida, 300 (B), sem ajuste -> vale zero
    e5  modificativa, aprovada, 50 (A)
    e6  diversos, aprovada, 200 (B), com o ajuste aj2 -> vale zero
    aj1 diversos, em execução, A 450, da e3, com unidade
    aj2 diversos, registrado, A 100 e B 150, das e3 e e6
    aj3 saúde, impedido, B 70, sem emenda -> vale zero
    emp1 ligado à e3 e ao aj1 (conta uma vez); emp2 ligado à e1
    """
    a, b = parlamentar, parlamentar_b
    entidade = mommy.make(Entidade, nome_fantasia="Casa Abrigo", _fill_optional=False)

    def emenda(tipo, fase, valor, dono, **kwargs):
        return make_emenda(
            tipo=tipo, fase=fase, valor=Decimal(valor), parlamentar=dono, **kwargs
        )

    e1 = emenda(EmendaLoa.DIVERSOS, 30, "1000.00", a, entidade=entidade)
    e2 = emenda(EmendaLoa.SAUDE, 60, "600.00", None)
    EmendaLoaParlamentar.objects.create(emendaloa=e2, parlamentar=a, valor=400)
    EmendaLoaParlamentar.objects.create(emendaloa=e2, parlamentar=b, valor=200)
    e3 = emenda(EmendaLoa.DIVERSOS, 30, "500.00", a)
    e4 = emenda(EmendaLoa.DIVERSOS, 40, "300.00", b)
    e5 = emenda(EmendaLoa.MODIFICATIVA, 30, "50.00", a)
    e6 = emenda(EmendaLoa.DIVERSOS, 30, "200.00", b)

    aj1 = _ajuste(loa, 1, 99, 60, [(a, "450.00")], emendas=[e3], unidade=unidade)
    aj2 = _ajuste(loa, 2, 99, 10, [(a, "100.00"), (b, "150.00")], emendas=[e3, e6])
    aj3 = _ajuste(loa, 3, 10, 40, [(b, "70.00")])

    # o texto de busca é montado no save(); aqui vai direto, para o filtro
    EmendaLoa.objects.filter(pk=e1.pk).update(search="reforma da creche")
    RegistroAjusteLoa.objects.filter(pk=aj1.pk).update(search="creche nova")

    emp1 = _empenho(loa, "100.00", "80.00", "60.00", "5.00")
    emp2 = _empenho(loa, "200.00", "150.00", "120.00", "0.00")
    EmpenhoEmendaAjuste.objects.create(emendaloa=e3, empenho=emp1)
    EmpenhoEmendaAjuste.objects.create(ajuste=aj1, empenho=emp1)
    EmpenhoEmendaAjuste.objects.create(emendaloa=e1, empenho=emp2)

    return {
        "loa": loa,
        "a": a,
        "b": b,
        "unidade": unidade,
        "entidade": entidade,
        "emendas": [e1, e2, e3, e4, e5, e6],
        "ajustes": [aj1, aj2, aj3],
    }


def _rota(loa, consulta):
    return f"/api/loa/loa/{loa.pk}/prestacaoconta_{consulta}/"


CONSULTAS = ["resumo", "dashboard", "itens", "opcoes"]


# ------------------------------------------------- requisitos de segurança


@pytest.mark.spec("LOA-PCC-060")
@pytest.mark.parametrize("consulta", CONSULTAS)
def test_consulta_e_publica_e_so_de_leitura(cenario, consulta):
    client = APIClient()
    rota = _rota(cenario["loa"], consulta)

    assert client.get(rota).status_code == 200
    assert client.post(rota, {}).status_code in (401, 403, 405)


@pytest.mark.spec("LOA-PCC-060")
@pytest.mark.parametrize("consulta", CONSULTAS)
def test_loa_que_o_usuario_nao_ve_responde_404(legislatura_atual, consulta):
    nao_publicada = _loa(2028, publicado=False)

    assert APIClient().get(_rota(nao_publicada, consulta)).status_code == 404


@pytest.mark.spec("LOA-PCC-060")
@pytest.mark.parametrize("consulta", CONSULTAS)
def test_editor_da_contabilidade_consulta_loa_nao_publicada(
    legislatura_atual, editor_contabil, consulta
):
    nao_publicada = _loa(2028, publicado=False)
    client = APIClient()
    client.force_authenticate(user=editor_contabil)

    assert client.get(_rota(nao_publicada, consulta)).status_code == 200


@pytest.mark.spec("LOA-PCC-005")
@pytest.mark.parametrize("consulta", CONSULTAS)
def test_loa_sem_norma_ou_anterior_ao_ano_inicial_responde_404(
    legislatura_atual, consulta
):
    sem_norma = _loa(2029, com_norma=False)
    antiga = _loa(2022)

    assert APIClient().get(_rota(sem_norma, consulta)).status_code == 404
    assert APIClient().get(_rota(antiga, consulta)).status_code == 404


@pytest.mark.spec("LOA-PCC-060")
@pytest.mark.parametrize("consulta", CONSULTAS)
def test_exercicio_extra_indisponivel_responde_400_sem_dizer_o_motivo(
    cenario, consulta
):
    nao_publicada = _loa(2028, publicado=False)
    sem_norma = _loa(2029, com_norma=False)
    rota = _rota(cenario["loa"], consulta)

    respostas = [
        APIClient().get(rota, {"loas": str(pk)})
        for pk in (nao_publicada.pk, sem_norma.pk, 999999)
    ]

    assert [r.status_code for r in respostas] == [400, 400, 400]
    assert len({str(r.json()) for r in respostas}) == 1


@pytest.mark.spec("LOA-PCC-063")
def test_mais_de_dez_exercicios_extras_responde_400(cenario):
    loas = ",".join(str(cenario["loa"].pk) for _ in range(11))

    resposta = APIClient().get(_rota(cenario["loa"], "resumo"), {"loas": loas})

    assert resposta.status_code == 400
    assert "loas" in resposta.json()


@pytest.mark.spec("LOA-PCC-004")
@pytest.mark.parametrize(
    "parametros",
    [
        {"unidade": "abc"},
        {"unidade": "999999"},
        {"entidade": "999999"},
        {"parlamentar": "999999"},
        {"tipo__in": "7"},
        {"tipo__in": "10,x"},
        {"loas": "abc"},
        {"page": "0"},
    ],
)
def test_filtro_invalido_responde_400(cenario, parametros):
    for consulta in CONSULTAS:
        resposta = APIClient().get(_rota(cenario["loa"], consulta), parametros)
        if consulta != "itens" and "page" in parametros:
            continue
        if consulta == "opcoes" and "loas" not in parametros:
            # das opções, só os exercícios contam: os outros filtros não chegam
            # ao serviço
            if set(parametros) & {"unidade", "entidade", "parlamentar"}:
                continue
        assert resposta.status_code == 400, (consulta, resposta.content)
        assert set(resposta.json()) == set(parametros)


def _chaves(valor):
    if isinstance(valor, dict):
        for chave, sub in valor.items():
            yield chave
            yield from _chaves(sub)
    elif isinstance(valor, list):
        for sub in valor:
            yield from _chaves(sub)


@pytest.mark.spec("LOA-PCC-061")
@pytest.mark.parametrize("consulta", CONSULTAS)
def test_resposta_nao_traz_campos_internos(cenario, superuser, consulta):
    # nem para superusuário: a consulta só entrega o que a tela mostra
    client = APIClient()
    client.force_authenticate(user=superuser)

    dados = client.get(_rota(cenario["loa"], consulta), {"page_size": 100}).json()

    proibidas = {"owner", "modifier", "metadata", "search", "ip", "user", "cpfcnpj"}
    assert not proibidas & set(_chaves(dados))


def _consultas_ao_banco(rota, **parametros):
    client = APIClient()
    with CaptureQueriesContext(connection) as capturadas:
        assert client.get(rota, parametros).status_code == 200
    return len(capturadas)


@pytest.mark.spec("LOA-PCC-062")
@pytest.mark.parametrize(
    "consulta, teto",
    [("resumo", 16), ("dashboard", 18), ("itens", 22), ("opcoes", 12)],
)
def test_custo_nao_depende_da_quantidade_de_itens(cenario, make_emenda, consulta, teto):
    rota = _rota(cenario["loa"], consulta)
    antes = _consultas_ao_banco(rota, page_size=100)

    a, b = cenario["a"], cenario["b"]
    for i in range(12):
        emenda = make_emenda(
            tipo=EmendaLoa.DIVERSOS,
            fase=30,
            valor=Decimal("10.00"),
            parlamentar=a if i % 2 else b,
        )
        if i % 3 == 0:
            _ajuste(cenario["loa"], 10 + i, 99, 60, [(a, "5.00")], emendas=[emenda])

    depois = _consultas_ao_banco(rota, page_size=100)

    assert depois == antes
    assert depois <= teto


@pytest.mark.spec("LOA-PCC-064")
def test_busca_com_texto_qualquer_nao_quebra_a_consulta(cenario):
    for texto in ["'; DROP TABLE loa_emendaloa; --", "%_\\", "a" * 150]:
        resposta = APIClient().get(_rota(cenario["loa"], "resumo"), {"search": texto})
        assert resposta.status_code == 200
        assert resposta.json()["itens"] == 0
    assert EmendaLoa.objects.count() == 6


# ------------------------------------------------------- regras, no serviço


def _resumo(cenario, **filtros):
    return servico.resumo(ANONIMO, cenario["loa"], filtros)


def _grupo(resumo, nome):
    return (resumo[nome]["valor"], resumo[nome]["quantidade"])


@pytest.mark.spec("LOA-PCC-010")
@pytest.mark.spec("LOA-PCC-011")
@pytest.mark.spec("LOA-PCC-020")
def test_resumo_soma_o_valor_final_de_cada_item(cenario):
    resumo = _resumo(cenario)

    # e3 e e6 (com ajuste), e4 e aj3 (impedidos) valem zero; aj2, de duas
    # emendas, conta uma vez
    assert resumo["itens"] == 9
    assert _grupo(resumo, "impositivas") == ("2300.00", 8)
    assert _grupo(resumo, "saude") == ("600.00", 2)
    assert _grupo(resumo, "areas_diversas") == ("1700.00", 6)
    assert _grupo(resumo, "modificativas") == ("50.00", 1)


@pytest.mark.spec("LOA-PCC-012")
def test_resumo_com_filtro_de_parlamentar_usa_a_parte_dele(cenario):
    resumo = _resumo(cenario, parlamentar=cenario["a"].pk)

    # e1 1000, e2 400 (parte de A), e3 zero, aj1 450, aj2 100 (parte de A)
    assert _grupo(resumo, "impositivas") == ("1950.00", 5)
    assert _grupo(resumo, "saude") == ("400.00", 1)
    assert _grupo(resumo, "modificativas") == ("50.00", 1)

    resumo = _resumo(cenario, parlamentar=cenario["b"].pk)

    # e2 200, e4 e e6 zero, aj2 150, aj3 impedido zero
    assert _grupo(resumo, "impositivas") == ("350.00", 5)


@pytest.mark.spec("LOA-PCC-002")
@pytest.mark.spec("LOA-PCC-023")
def test_filtro_de_documentos_e_aviso_das_emendas_zeradas(cenario):
    so_emendas = _resumo(cenario, tipos=[10, 99])
    assert so_emendas["itens"] == 5
    assert _grupo(so_emendas, "impositivas") == ("1600.00", 5)
    assert so_emendas["emendas_com_valor_em_ajuste"] == {
        "quantidade": 2,
        "valor_original": "700.00",
    }
    assert so_emendas["emendas_em_impedimento"] == {
        "quantidade": 1,
        "valor_original": "300.00",
    }

    so_ajustes = _resumo(cenario, ajustes=True)
    assert so_ajustes["itens"] == 3
    assert _grupo(so_ajustes, "impositivas") == ("700.00", 3)

    os_dois = _resumo(cenario, tipos=[10], ajustes=True)
    assert os_dois["itens"] == 2  # e2 e aj3, os de saúde
    assert _grupo(os_dois, "impositivas") == ("600.00", 2)

    tudo = _resumo(cenario)
    assert tudo["itens"] == 9


@pytest.mark.spec("LOA-PCC-021")
def test_execucao_conta_cada_empenho_uma_vez(cenario):
    execucao = _resumo(cenario)["execucao"]

    # emp1 está ligado à e3 e ao aj1
    assert execucao["empenhado"] == "300.00"
    assert execucao["liquidado"] == "230.00"
    assert execucao["pago_bruto"] == "180.00"
    assert execucao["anulado"] == "5.00"

    so_ajustes = _resumo(cenario, ajustes=True)["execucao"]
    assert so_ajustes["empenhado"] == "100.00"


@pytest.mark.spec("LOA-PCC-003")
@pytest.mark.spec("LOA-PCC-022")
@pytest.mark.spec("LOA-PCC-024")
def test_exercicios_extras_entram_na_mesma_conta(cenario, parlamentar):
    anterior = _loa(2025)
    _loa(2028, publicado=False)
    _loa(2029, com_norma=False)
    _loa(2022)
    _ajuste(anterior, 9, 10, 60, [(parlamentar, "40.00")])

    so_a_da_rota = _resumo(cenario)
    assert so_a_da_rota["execucao"]["vale"] is True
    assert so_a_da_rota["exercicios"] == [
        {"id": cenario["loa"].pk, "ano": 2027, "selecionado": True},
        {"id": anterior.pk, "ano": 2025, "selecionado": False},
    ]

    com_extra = _resumo(cenario, loas=[anterior.pk])
    assert com_extra["itens"] == 10
    assert _grupo(com_extra, "saude") == ("640.00", 3)
    # 2025 é anterior ao ano inicial da execução
    assert com_extra["execucao"]["vale"] is False
    assert [e["selecionado"] for e in com_extra["exercicios"]] == [True, True]


@pytest.mark.spec("LOA-PCC-001")
@pytest.mark.parametrize(
    "filtros",
    [
        {},
        {"situacao": "IMPEDIMENTO"},
        {"situacao": "REGISTRADO,EM_EXECUCAO"},
        {"search": "creche"},
        {"unidade": "U"},
        {"entidade": "E"},
        {"parlamentar": "B"},
    ],
)
def test_filtros_selecionam_os_mesmos_registros_das_rotas_atuais(cenario, filtros):
    troca = {
        "U": cenario["unidade"].pk,
        "E": cenario["entidade"].pk,
        "B": cenario["b"].pk,
    }
    filtros = {k: troca.get(v, v) for k, v in filtros.items()}
    client = APIClient()
    loa = cenario["loa"]

    novos = client.get(_rota(loa, "itens"), {**filtros, "page_size": 100}).json()
    novos = {(i["classe"], i["id"]) for i in novos["results"]}

    atuais = dict(filtros)
    if "parlamentar" in atuais:
        atuais["parlamentares"] = atuais["parlamentares_valor"] = atuais.pop(
            "parlamentar"
        )
    emendas = client.get(
        "/api/loa/emendaloa/",
        {**atuais, "loa": loa.pk, "include": "id", "page_size": 100},
    ).json()
    ajustes = client.get(
        "/api/loa/registroajusteloa/",
        {**atuais, "oficio_ajuste_loa__loa": loa.pk, "include": "id", "page_size": 100},
    ).json()
    esperados = {("emenda", i["id"]) for i in emendas["results"]}
    esperados |= {("ajuste", i["id"]) for i in ajustes["results"]}

    assert novos == esperados
    assert novos


def _dashboard(cenario, **filtros):
    return servico.dashboard(ANONIMO, cenario["loa"], filtros)


def _por_nome(lista):
    return {i["nome"]: i for i in lista}


@pytest.mark.spec("LOA-PCC-013")
@pytest.mark.spec("LOA-PCC-031")
def test_dashboard_por_parlamentar_em_areas_diversas(cenario):
    parlamentares = _dashboard(cenario)["parlamentares"]

    # A: e1 1000, e3 zero, aj1 450, aj2 100; B: e4 e e6 zero, aj2 150
    assert [
        (p["nome"], p["valor"], p["emendas"], p["ajustes"]) for p in parlamentares
    ] == [
        ("Parlamentar A", "1550.00", 2, 2),
        ("Parlamentar B", "150.00", 2, 1),
    ]
    unidades_de_a = {u["nome"]: u["valor"] for u in parlamentares[0]["unidades"]}
    assert unidades_de_a == {"01 - Unidade Teste": "1450.00", None: "100.00"}


@pytest.mark.spec("LOA-PCC-032")
@pytest.mark.spec("LOA-PCC-033")
@pytest.mark.spec("LOA-PCC-034")
def test_dashboard_por_unidade_e_por_entidade(cenario):
    dashboard = _dashboard(cenario)

    (unidade,) = dashboard["unidades"]
    # e1, e3, e4, e6 e aj1; o aj2 não tem unidade
    assert (unidade["nome"], unidade["valor"], unidade["quantidade"]) == (
        "01 - Unidade Teste",
        "1450.00",
        5,
    )
    assert [(p["nome"], p["valor"]) for p in unidade["parlamentares"]] == [
        ("Parlamentar A", "1450.00"),
        ("Parlamentar B", "0.00"),
    ]

    (entidade,) = dashboard["entidades"]
    assert (entidade["nome"], entidade["valor"], entidade["quantidade"]) == (
        "Casa Abrigo",
        "1000.00",
        1,
    )


@pytest.mark.spec("LOA-PCC-030")
def test_dashboard_de_situacao_reune_emendas_e_ajustes(cenario, make_emenda):
    # uma emenda em execução do tipo 99, para dividir o grupo com o aj1
    make_emenda(
        tipo=EmendaLoa.DIVERSOS,
        fase=60,
        valor=Decimal("30.00"),
        parlamentar=cenario["b"],
    )

    diversas, saude = None, None
    for secao in _dashboard(cenario)["situacao"]:
        if secao["tipo"] == 99:
            diversas = secao["grupos"]
        else:
            saude = secao["grupos"]

    assert [(g["rotulo"], g["quantidade"], g["valor"]) for g in diversas] == [
        ("Aprovada", 3, "1000.00"),
        ("Em Execução", 2, "480.00"),
        ("Impedimento", 1, "0.00"),
        ("Registrado", 1, "250.00"),
    ]
    em_execucao = diversas[1]
    assert [(p["nome"], p["valor"]) for p in em_execucao["parlamentares"]] == [
        ("Parlamentar A", "450.00"),
        ("Parlamentar B", "30.00"),
    ]
    assert [(g["rotulo"], g["quantidade"], g["valor"]) for g in saude] == [
        ("Em Execução", 1, "600.00"),
        ("Impedimento", 1, "0.00"),
    ]


def _itens(cenario, **parametros):
    resposta = APIClient().get(_rota(cenario["loa"], "itens"), parametros)
    assert resposta.status_code == 200, resposta.content
    return resposta.json()


@pytest.mark.spec("LOA-PCC-040")
def test_itens_trazem_emendas_e_depois_ajustes_paginados_pelo_servidor(cenario):
    ids_emendas = [e.pk for e in cenario["emendas"]]
    ids_ajustes = [a.pk for a in cenario["ajustes"]]

    primeira = _itens(cenario, page_size=4)
    assert primeira["pagination"]["total_entries"] == 9
    assert primeira["pagination"]["total_pages"] == 3
    assert primeira["pagination"]["next_page"] == 2
    assert [(i["classe"], i["id"]) for i in primeira["results"]] == [
        ("emenda", pk) for pk in ids_emendas[:4]
    ]

    ultima = _itens(cenario, page_size=4, page=3)
    assert ultima["pagination"]["next_page"] is None
    assert [i["classe"] for i in ultima["results"]] == ["ajuste"]

    todas = _itens(cenario, page_size=100)["results"]
    assert [i["id"] for i in todas if i["classe"] == "emenda"] == ids_emendas
    # ajustes pela numeração: RAT 001, 002 e 003
    assert [i["id"] for i in todas if i["classe"] == "ajuste"] == ids_ajustes

    assert (
        APIClient().get(_rota(cenario["loa"], "itens"), {"page": 9}).status_code == 404
    )
    # o tamanho da página é limitado a 100
    assert len(_itens(cenario, page_size=5000)["results"]) == 9


@pytest.mark.spec("LOA-PCC-040")
def test_ajustes_saem_pela_numeracao_e_nao_pela_ordem_de_cadastro(cenario):
    aj1, aj2, aj3 = cenario["ajustes"]
    # cadastrado por último, com o menor número; o aj1 é renumerado para o fim
    aj0 = _ajuste(cenario["loa"], 0, 99, 60, [(cenario["b"], "10.00")])
    RegistroAjusteLoa.objects.filter(pk=aj1.pk).update(numero=9)

    ajustes = _itens(cenario, page_size=100, ajustes="True")["results"]

    assert [i["id"] for i in ajustes] == [aj0.pk, aj2.pk, aj3.pk, aj1.pk]


@pytest.mark.spec("LOA-PCC-044")
def test_toda_listagem_de_ajustes_sai_pela_numeracao(cenario):
    aj1, aj2, aj3 = cenario["ajustes"]
    aj0 = _ajuste(cenario["loa"], 0, 99, 60, [(cenario["b"], "10.00")])
    RegistroAjusteLoa.objects.filter(pk=aj1.pk).update(numero=9)
    esperada = [aj0.pk, aj2.pk, aj3.pk, aj1.pk]

    # a ordem padrão do model, que as telas e os relatórios herdam
    assert list(RegistroAjusteLoa.objects.values_list("pk", flat=True)) == esperada

    # as rotas atuais, mesmo quando o cliente pede outra ordem
    for parametros in ({}, {"o": "parlamentares_valor__nome_parlamentar"}):
        resposta = APIClient().get(
            "/api/loa/registroajusteloa/",
            {"include": "id", "page_size": 100, **parametros},
        )
        assert [i["id"] for i in resposta.json()["results"]] == esperada


@pytest.mark.spec("LOA-PCC-041")
@pytest.mark.spec("LOA-PCC-042")
@pytest.mark.spec("LOA-PCC-043")
@pytest.mark.spec("LOA-PCC-050")
def test_item_traz_o_que_o_cartao_mostra(cenario):
    e1, e2, e3 = cenario["emendas"][:3]
    aj1, aj2, aj3 = cenario["ajustes"]
    itens = {
        (i["classe"], i["id"]): i for i in _itens(cenario, page_size=100)["results"]
    }

    emenda = itens[("emenda", e3.pk)]
    assert emenda["valor_original"] == "500.00"
    assert emenda["valor_final"] == "0.00"
    assert emenda["tem_ajustes"] is True
    assert (emenda["tipo"], emenda["tipo_rotulo"]) == (99, "Em.Imp. Áreas Diversas")
    assert (emenda["fase"], emenda["fase_rotulo"]) == (30, "Aprovada")
    assert emenda["unidade"] == {
        "id": cenario["unidade"].pk,
        "nome": "01 - Unidade Teste",
    }
    assert emenda["entidade"] is None
    assert emenda["link"] == f"/loa/emendaloa/{e3.pk}"
    assert "Finalidade de teste" in emenda["objeto"]
    # dois ajustes; empenho da emenda e o do aj1
    assert emenda["abas"] == {
        "prestacao": 0,
        "ajustes": 2,
        "empenhos": 2,
        "tramitacoes": 0,
        "documentos": 0,
    }

    com_dois = itens[("emenda", e2.pk)]
    assert com_dois["valor_final"] == "600.00"
    assert [(p["nome"], p["valor"]) for p in com_dois["parlamentares"]] == [
        ("Parlamentar A", "400.00"),
        ("Parlamentar B", "200.00"),
    ]
    assert itens[("emenda", e1.pk)]["entidade"]["nome"] == "Casa Abrigo"
    assert itens[("emenda", e1.pk)]["abas"]["empenhos"] == 1

    ajuste = itens[("ajuste", aj2.pk)]
    assert ajuste["titulo"] == "RAT 002/2027 - Registro de Ajuste Técnico"
    assert (ajuste["valor"], ajuste["valor_final"]) == ("250.00", "250.00")
    assert [e["id"] for e in ajuste["emendas"]] == [e3.pk, cenario["emendas"][5].pk]
    assert set(ajuste["emendas"][0]) == {"id", "titulo"}
    assert ajuste["descricao"] == "Ajuste 2"
    assert ajuste["abas"] == {"prestacao": 0, "empenhos": 0}
    assert itens[("ajuste", aj1.pk)]["abas"]["empenhos"] == 1

    impedido = itens[("ajuste", aj3.pk)]
    assert (impedido["valor"], impedido["valor_final"]) == ("70.00", "0.00")
    assert impedido["fase_rotulo"] == "Impedimento Técnico"

    aj1.fase = RegistroAjusteLoa.AJUSTE_FINALIZADO
    aj1.save(auto_update_search=False)
    finalizado = _itens(cenario, page_size=100, ajustes="True")["results"]
    assert {i["fase_rotulo"] for i in finalizado if i["id"] == aj1.pk} == {"Finalizado"}


# ------------------------------------------------------ opções dos filtros


@pytest.mark.spec("LOA-PCC-090")
def test_opcoes_dos_filtros_sao_as_dos_exercicios_pedidos(cenario, parlamentar):
    loa = cenario["loa"]
    Entidade.objects.filter(pk=cenario["entidade"].pk).update(ativo=True)
    inativa = mommy.make(Entidade, nome_fantasia="Inativa", ativo=False)
    EmendaLoa.objects.filter(pk=cenario["emendas"][1].pk).update(entidade=inativa)
    mommy.make(UnidadeOrcamentaria, loa=loa, codigo="02", especificacao="Sem emenda")

    anterior = _loa(2025)
    unidade_antiga = mommy.make(
        UnidadeOrcamentaria,
        loa=anterior,
        codigo="09",
        especificacao="Antiga",
        recebe_emenda_impositiva=True,
    )
    outra = mommy.make(Entidade, nome_fantasia="Abrigo Antigo", ativo=True)
    ajuste = _ajuste(anterior, 9, 10, 60, [(parlamentar, "40.00")])
    RegistroAjusteLoa.objects.filter(pk=ajuste.pk).update(entidade=outra)

    so_a_da_rota = servico.opcoes(ANONIMO, loa, {})
    assert [p["nome"] for p in so_a_da_rota["parlamentares"]] == [
        "Parlamentar A",
        "Parlamentar B",
    ]
    # só as unidades que recebem emenda impositiva, só as entidades ativas
    assert so_a_da_rota["unidades"] == [
        {"id": cenario["unidade"].pk, "nome": "01 - Unidade Teste", "ano": 2027}
    ]
    assert [e["nome"] for e in so_a_da_rota["entidades"]] == ["Casa Abrigo"]
    assert set(so_a_da_rota["entidades"][0]) == {"id", "nome", "rotulo"}

    com_extra = servico.opcoes(ANONIMO, loa, {"loas": [anterior.pk]})
    assert [u["id"] for u in com_extra["unidades"]] == [
        cenario["unidade"].pk,
        unidade_antiga.pk,
    ]
    assert [e["nome"] for e in com_extra["entidades"]] == [
        "Abrigo Antigo",
        "Casa Abrigo",
    ]


# ------------------------------------------------- relatório para impressão


def _relatorio(loa, **parametros):
    """O relatório de ``/loa/<pk>/prestacaoconta?print=True``, depois do
    reCAPTCHA."""
    url = f"/loa/{loa.pk}/prestacaoconta?" + urlencode({"print": "True", **parametros})
    with mock.patch.object(
        GoogleRecapthaViewMixin, "_validate_recaptcha", return_value=True
    ):
        return Client().post(url, {"g-recaptcha-response": "token"})


def _blocos(resposta):
    html = resposta.content.decode()
    return html.count('class="emenda-item"'), html.count('class="ajuste-item"')


@pytest.mark.spec("LOA-PCC-070")
@pytest.mark.spec("LOA-PCT-066")
def test_relatorio_traz_os_itens_que_o_servico_seleciona(cenario):
    loa = cenario["loa"]

    completo = _relatorio(loa)
    assert completo.status_code == 200
    assert _blocos(completo) == (6, 3)

    assert _blocos(_relatorio(loa, tipo__in="10,99")) == (5, 0)
    assert _blocos(_relatorio(loa, ajustes="True")) == (0, 3)
    assert _blocos(_relatorio(loa, ajustes="True", tipo__in="10")) == (1, 1)
    # e2, e4 e e6 são do parlamentar B; aj2 e aj3 também
    assert _blocos(_relatorio(loa, parlamentares=cenario["b"].pk)) == (3, 2)
    assert _blocos(_relatorio(loa, situacao="IMPEDIMENTO")) == (1, 1)


@pytest.mark.spec("LOA-PCC-070")
@pytest.mark.spec("LOA-PCT-066")
def test_relatorio_mostra_o_valor_final_das_emendas_zeradas(cenario):
    html = _relatorio(cenario["loa"]).content.decode()

    # e3 e e6 têm ajuste; e4 está em impedimento
    assert html.count("<dt>Valor Final:</dt>") == 3
    assert html.count("valor remanejado para os registros de ajuste") == 2
    assert html.count("(impedimento técnico)") == 1


@pytest.mark.spec("LOA-PCT-067")
def test_relatorio_mostra_as_situacoes_do_filtro_com_o_nome_legivel(cenario):
    html = _relatorio(
        cenario["loa"], situacao="EM_EXECUCAO,REGISTRADO"
    ).content.decode()
    assert "<strong>Situação:</strong> Em Execução, Registrado" in html
    # o valor cru ainda aparece na URL da própria página, mas não no texto dos filtros
    assert "</strong> EM_EXECUCAO" not in html and ",REGISTRADO<" not in html

    todas = "REGISTRADO,IMPEDIMENTO,EM_EXECUCAO,FINALIZADO"
    html = _relatorio(cenario["loa"], situacao=todas).content.decode()
    assert (
        "<strong>Situação:</strong> Registrado, Impedimento, Em Execução, Finalizado"
        in html
    )
    # o filtro continua valendo: só o que está em impedimento
    assert _blocos(_relatorio(cenario["loa"], situacao="IMPEDIMENTO")) == (1, 1)


@pytest.mark.spec("LOA-PCC-070")
@pytest.mark.spec("LOA-PCT-066")
def test_relatorio_cobre_os_exercicios_extras_pedidos(cenario, parlamentar):
    anterior = _loa(2025)
    _ajuste(anterior, 9, 10, 60, [(parlamentar, "40.00")])

    com_extra = _relatorio(cenario["loa"], loas=anterior.pk)

    assert _blocos(com_extra) == (6, 4)
    assert "<strong>Exercícios:</strong> 2027, 2025" in com_extra.content.decode()
    assert "Exercícios:" not in _relatorio(cenario["loa"]).content.decode()


@pytest.mark.spec("LOA-PCC-070")
@pytest.mark.spec("LOA-PCT-066")
@pytest.mark.parametrize(
    "parametros",
    [{"unidade": "abc"}, {"unidade": "999999"}, {"tipo__in": "7"}, {"loas": "999999"}],
)
def test_relatorio_com_filtro_invalido_responde_400(cenario, parametros):
    resposta = _relatorio(cenario["loa"], **parametros)

    assert resposta.status_code == 400
    assert "Filtro inválido" in resposta.content.decode()


@pytest.mark.spec("LOA-PCC-070")
@pytest.mark.spec("LOA-PCT-066")
def test_custo_do_relatorio_nao_depende_da_quantidade_de_itens(cenario, make_emenda):
    def consultas():
        with CaptureQueriesContext(connection) as capturadas:
            assert _relatorio(cenario["loa"]).status_code == 200
        return len(capturadas)

    antes = consultas()
    a, b = cenario["a"], cenario["b"]
    for i in range(12):
        emenda = make_emenda(
            tipo=EmendaLoa.DIVERSOS,
            fase=30,
            valor=Decimal("10.00"),
            parlamentar=a if i % 2 else b,
        )
        if i % 3 == 0:
            _ajuste(cenario["loa"], 10 + i, 99, 60, [(a, "5.00")], emendas=[emenda])

    assert consultas() == antes


# ------------------------------- rotas loa/emendaloa e loa/registroajusteloa


def _lista(rota, **parametros):
    resposta = APIClient().get(f"/api/loa/{rota}/", {"page_size": 100, **parametros})
    assert resposta.status_code == 200, resposta.content
    return {i["id"]: i for i in resposta.json()["results"]}


@pytest.mark.spec("LOA-PCC-080")
def test_campos_calculados_das_rotas_de_emenda_e_de_ajuste(cenario):
    a, b = str(cenario["a"].pk), str(cenario["b"].pk)
    e1, e2, e3, e4 = cenario["emendas"][:4]
    aj1, aj2, aj3 = cenario["ajustes"]

    emendas = _lista("emendaloa", loa=cenario["loa"].pk)
    assert (emendas[e1.pk]["valor_computado"], emendas[e1.pk]["has_ajustes"]) == (
        1000.0,
        False,
    )
    assert emendas[e1.pk]["soma_valor_empenhado"] == 200.0
    assert emendas[e2.pk]["valor_inicial_por_parlamentar"] == {a: 400.0, b: 200.0}
    # e3 tem ajustes; e4 está em impedimento
    assert (emendas[e3.pk]["valor_computado"], emendas[e3.pk]["has_ajustes"]) == (
        0.0,
        True,
    )
    assert emendas[e3.pk]["str_valor_computado"] == "0,00"
    assert [
        emendas[e3.pk][f"soma_valor_{campo}"]
        for campo in ("empenhado", "liquidado", "pago_bruto", "anulado")
    ] == [100.0, 80.0, 60.0, 5.0]
    assert (emendas[e4.pk]["valor_computado"], emendas[e4.pk]["has_ajustes"]) == (
        0.0,
        False,
    )
    assert emendas[e4.pk]["soma_valor_empenhado"] == 0.0

    ajustes = _lista("registroajusteloa", oficio_ajuste_loa__loa=cenario["loa"].pk)
    assert ajustes[aj2.pk]["valor"] == 250.0
    assert ajustes[aj2.pk]["valor_por_parlamentar"] == {a: 100.0, b: 150.0}
    assert ajustes[aj2.pk]["valor_computado"] == 250.0
    assert sorted(ajustes[aj2.pk]["emendaloa"]) == sorted(
        [e3.pk, cenario["emendas"][5].pk]
    )
    assert ajustes[aj1.pk]["soma_valor_empenhado"] == 100.0
    # impedido: a soma continua, o valor computado e as partes zeram
    assert (ajustes[aj3.pk]["valor"], ajustes[aj3.pk]["valor_computado"]) == (
        70.0,
        0.0,
    )
    assert ajustes[aj3.pk]["valor_por_parlamentar"] == {b: 0.0}


@pytest.mark.spec("LOA-PCC-080")
@pytest.mark.parametrize(
    "rota, filtro, teto",
    [("emendaloa", "loa", 20), ("registroajusteloa", "oficio_ajuste_loa__loa", 20)],
)
def test_custo_das_listas_de_emenda_e_de_ajuste_nao_depende_da_quantidade(
    cenario, make_emenda, rota, filtro, teto
):
    def consultas():
        with CaptureQueriesContext(connection) as capturadas:
            _lista(rota, **{filtro: cenario["loa"].pk})
        return len(capturadas)

    antes = consultas()
    a, b = cenario["a"], cenario["b"]
    for i in range(12):
        emenda = make_emenda(
            tipo=EmendaLoa.DIVERSOS,
            fase=30,
            valor=Decimal("10.00"),
            parlamentar=a if i % 2 else b,
        )
        _ajuste(cenario["loa"], 10 + i, 99, 60, [(a, "5.00")], emendas=[emenda])

    depois = consultas()

    assert depois == antes
    assert depois <= teto
