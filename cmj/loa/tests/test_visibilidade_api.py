"""Consulta pela API dos registros que pertencem a uma LOA (API-ACS-051)."""

import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker as mommy
from rest_framework.test import APIClient

import sapl.api.urls  # noqa: F401  (registra os viewsets)
from cmj.loa.models import (
    Empenho,
    EmpenhoEmendaAjuste,
    Loa,
    OficioAjusteLoa,
    Orgao,
    PrestacaoContaLoa,
    PrestacaoContaRegistro,
    RegistroAjusteLoa,
    UnidadeOrcamentaria,
)

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.spec("API-ACS-051"),
    pytest.mark.spec("LOA-PCL-086"),
]


def _registros_da_loa(loa):
    """Um registro de cada rota consultada, pertencente a ``loa``."""
    oficio = mommy.make(OficioAjusteLoa, loa=loa)
    # o hook de busca do ajuste lê o M2M antes de haver pk
    ajuste = mommy.prepare(
        RegistroAjusteLoa, numero=1, ano=loa.ano, oficio_ajuste_loa=oficio
    )
    ajuste.save(auto_update_search=False)
    orgao = mommy.make(Orgao, loa=loa, codigo="01")
    empenho = mommy.make(Empenho, orgao=orgao, _fill_optional=False)
    prestacao = mommy.make(PrestacaoContaLoa, loa=loa)
    return {
        "loa": loa.pk,
        "oficioajusteloa": oficio.pk,
        "registroajusteloa": ajuste.pk,
        "orgao": orgao.pk,
        "unidadeorcamentaria": mommy.make(UnidadeOrcamentaria, loa=loa).pk,
        "empenho": empenho.pk,
        "empenhoemendaajuste": EmpenhoEmendaAjuste.objects.create(
            ajuste=ajuste, empenho=empenho
        ).pk,
        "prestacaocontaloa": prestacao.pk,
        "prestacaocontaregistro": mommy.make(
            PrestacaoContaRegistro, prestacao_conta=prestacao, _fill_optional=False
        ).pk,
    }


ROTAS = [
    "loa",
    "oficioajusteloa",
    "registroajusteloa",
    "orgao",
    "unidadeorcamentaria",
    "empenho",
    "empenhoemendaajuste",
    "prestacaocontaloa",
    "prestacaocontaregistro",
]


@pytest.fixture
def registros(loa):
    nao_publicada = mommy.make(Loa, ano=2090, publicado=False)
    return {
        "publicada": _registros_da_loa(loa),
        "nao_publicada": _registros_da_loa(nao_publicada),
    }


@pytest.fixture
def cliente(request, autor, editor_contabil):
    perfil = request.param
    client = APIClient()
    usuarios = {
        "comum": lambda: get_user_model().objects.create_user(
            email="comum@test.local", password="testpass123!"
        ),
        "autor": lambda: autor,
        "editor": lambda: editor_contabil,
    }
    if perfil in usuarios:
        client.force_authenticate(user=usuarios[perfil]())
    return perfil, client


def _ids(client, rota, **params):
    resposta = client.get(f"/api/loa/{rota}/", {"include": "id", **params})
    assert resposta.status_code == 200, resposta.content
    return {item["id"] for item in resposta.json()["results"]}


@pytest.mark.parametrize("rota", ROTAS)
@pytest.mark.parametrize(
    "cliente, ve_nao_publicada",
    [("anonimo", False), ("comum", False), ("autor", True), ("editor", True)],
    indirect=["cliente"],
)
def test_lista_segue_a_visibilidade_da_loa(registros, rota, cliente, ve_nao_publicada):
    _, client = cliente
    ids = _ids(client, rota, page_size=100)

    assert registros["publicada"][rota] in ids
    assert (registros["nao_publicada"][rota] in ids) is ve_nao_publicada


@pytest.mark.parametrize("rota", ROTAS)
def test_detalhe_de_loa_nao_publicada_responde_404_a_anonimo(registros, rota):
    client = APIClient()
    publicada = registros["publicada"][rota]
    nao_publicada = registros["nao_publicada"][rota]

    assert client.get(f"/api/loa/{rota}/{publicada}/?include=id").status_code == 200
    resposta = client.get(f"/api/loa/{rota}/{nao_publicada}/?include=id")
    assert resposta.status_code == 404


def test_operador_de_autor_nao_ve_loa_nao_publicada_cuja_materia_virou_norma(
    registros, autor
):
    from sapl.materia.models import MateriaLegislativa
    from sapl.norma.models import NormaJuridica

    nao_publicada = Loa.objects.get(pk=registros["nao_publicada"]["loa"])
    if nao_publicada.materia is None:
        nao_publicada.materia = mommy.make(MateriaLegislativa, _fill_optional=False)
        nao_publicada.save()
    mommy.make(NormaJuridica, materia=nao_publicada.materia, _fill_optional=False)

    client = APIClient()
    client.force_authenticate(user=autor)
    ids = _ids(client, "oficioajusteloa")

    assert ids == {registros["publicada"]["oficioajusteloa"]}


def test_totais_dos_ajustes_seguem_a_visibilidade_da_loa(registros):
    nao_publicada = Loa.objects.get(pk=registros["nao_publicada"]["loa"])
    resposta = APIClient().get(
        "/api/loa/registroajusteloa/totalize_empenhos/",
        {"oficio_ajuste_loa__loa": nao_publicada.pk},
    )

    assert resposta.status_code == 200
    assert resposta.json()["total_empenhado"] is None


def test_escrita_nao_e_afetada_pela_visibilidade(registros, superuser):
    """A escrita continua decidida pelas permissões de edição: quem grava acha
    o registro mesmo sem vê-lo pela regra da consulta."""
    nao_publicada = registros["nao_publicada"]["oficioajusteloa"]
    client = APIClient()
    client.force_authenticate(user=superuser)

    resposta = client.patch(
        f"/api/loa/oficioajusteloa/{nao_publicada}/?include=id", {"epigrafe": "x"}
    )

    assert resposta.status_code == 200
