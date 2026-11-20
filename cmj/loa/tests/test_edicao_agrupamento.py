"""Testes da spec docs/specs/loa/edicao-agrupamento.md."""

from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.messages import get_messages
from model_mommy import mommy

from cmj.loa.models import (
    AgrupamentoEmendaLoa,
    AgrupamentoRegistroContabil,
    Despesa,
    EmendaLoa,
)
from cmj.loa.tests.conftest import recarregar

pytestmark = pytest.mark.django_db

P = EmendaLoa.PROPOSTA  # 10
EC = EmendaLoa.EDICAO_CONTABIL  # 15
LC = EmendaLoa.LIBERACAO_CONTABIL  # 17


@pytest.fixture
def agrupamento_liberavel(agrupamento, loa):
    """Agrupamento com registros contábeis que somam zero."""
    for percentual in (Decimal("-100.00"), Decimal("100.00")):
        AgrupamentoRegistroContabil.objects.create(
            agrupamento=agrupamento,
            despesa=mommy.make(Despesa, loa=loa),
            percentual=percentual,
        )
    return agrupamento


@pytest.fixture(autouse=True)
def _sem_artigos():
    """Os artigos da emenda consultam a view SQL loa_despesa_consulta, ausente nos testes."""
    with mock.patch.object(
        EmendaLoa, "artigos", new_callable=mock.PropertyMock, return_value=[]
    ):
        yield


def liberar(client, agrupamento):
    return client.post(
        f"/loa/agrupamento/{agrupamento.pk}/edit",
        {"nome": agrupamento.nome, "tipo": agrupamento.tipo, "ano_loa": "x"},
    )


@pytest.mark.spec("LOA-AGR-082")
def test_liberacao_bloqueada_com_emenda_devolvida(
    client, editor_contabil, make_emenda, agrupamento_liberavel
):
    ok = make_emenda(fase=EC)
    devolvida = make_emenda(fase=EC)
    for el in (ok, devolvida):
        AgrupamentoEmendaLoa.objects.create(
            agrupamento=agrupamento_liberavel, emendaloa=el
        )
    EmendaLoa.objects.filter(pk=devolvida.pk).update(fase=P)

    client.force_login(editor_contabil)
    r = liberar(client, agrupamento_liberavel)

    assert r.status_code == 200
    assert "emendas devolvidas para correção" in r.content.decode()
    assert recarregar(ok).fase == EC
    assert recarregar(devolvida).fase == P


@pytest.mark.spec("LOA-AGR-082")
def test_liberacao_bloqueada_com_coletiva_devolvida(
    client, editor_contabil, make_emenda, agrupamento_liberavel
):
    coletiva = make_emenda(fase=P)
    coletiva.agrupamento_de_origem = agrupamento_liberavel
    coletiva.save()

    client.force_login(editor_contabil)
    r = liberar(client, agrupamento_liberavel)

    assert r.status_code == 200
    assert "emendas devolvidas para correção" in r.content.decode()
    assert recarregar(coletiva).fase == P


@pytest.mark.spec("LOA-AGR-081")
def test_liberacao_sem_devolvidas_leva_para_17(
    client, editor_contabil, make_emenda, agrupamento_liberavel
):
    el = make_emenda(fase=EC)
    AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento_liberavel, emendaloa=el)

    client.force_login(editor_contabil)
    r = liberar(client, agrupamento_liberavel)

    assert r.status_code == 302
    assert recarregar(el).fase == LC


def mensagens(response):
    return [(m.level_tag, str(m)) for m in get_messages(response.wsgi_request)]


@pytest.mark.spec("LOA-AGR-083")
def test_liberacao_sem_gerar_coletivas_libera_e_informa(
    client, editor_contabil, make_emenda, agrupamento_liberavel
):
    juntaveis = [make_emenda(fase=EC, permite_juncao_coletiva=True) for _ in range(2)]
    for el in juntaveis:
        AgrupamentoEmendaLoa.objects.create(
            agrupamento=agrupamento_liberavel, emendaloa=el
        )

    client.force_login(editor_contabil)
    r = liberar(client, agrupamento_liberavel)

    assert r.status_code == 302
    assert all(recarregar(el).fase == LC for el in juntaveis)
    assert not agrupamento_liberavel.emendas_coletivas_geradas.exists()
    assert (
        "info",
        "2 emenda(s) que permitem junção em emenda coletiva foram liberadas "
        "individualmente, sem junção.",
    ) in mensagens(r)


@pytest.mark.spec("LOA-AGR-083")
def test_liberacao_nao_informa_quando_nao_ha_conjunto_para_juntar(
    client, editor_contabil, make_emenda, agrupamento_liberavel
):
    sozinha = make_emenda(fase=EC, permite_juncao_coletiva=True)
    sem_juncao = make_emenda(fase=EC, permite_juncao_coletiva=False)
    for el in (sozinha, sem_juncao):
        AgrupamentoEmendaLoa.objects.create(
            agrupamento=agrupamento_liberavel, emendaloa=el
        )

    client.force_login(editor_contabil)
    r = liberar(client, agrupamento_liberavel)

    assert r.status_code == 302
    assert recarregar(sozinha).fase == LC
    assert not [m for m in mensagens(r) if m[0] == "info"]
