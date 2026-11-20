"""Testes da spec docs/specs/loa/edicao-agrupamento.md."""

from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.messages import get_messages
from model_mommy import mommy

from cmj.loa.models import (
    Agrupamento,
    AgrupamentoEmendaLoa,
    AgrupamentoRegistroContabil,
    Despesa,
    EmendaLoa,
    EmendaLoaRegistroContabil,
    UnidadeOrcamentaria,
)
from cmj.loa.models.m_agrupamento import FinalidadeManualRemovida
from cmj.loa.tests.conftest import recarregar
from cmj.utils.genia.loa_agrupamento import IAEmentaEmendaColetivaError

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


# ------------------------------------------------- finalidade digitada (D3)

# lido no import, antes do mock autouse do conftest
UPDATE_FINALIDADE_ORIGINAL = Agrupamento.update_finalidade_com_ia
GERAR = "cmj.loa.models.m_agrupamento.IAEmentaEmendaColetiva.gerar_finalidade_global"


@pytest.fixture
def ia_real():
    """Desfaz o mock de update_finalidade_com_ia do conftest."""
    with mock.patch.object(
        Agrupamento, "update_finalidade_com_ia", UPDATE_FINALIDADE_ORIGINAL
    ):
        yield


@pytest.fixture
def com_emenda(agrupamento, make_emenda):
    el = make_emenda(fase=EC)
    AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento, emendaloa=el)
    return agrupamento


def digitar(client, agrupamento, texto):
    return client.patch(
        f"/api/loa/agrupamento/{agrupamento.pk}/", {"finalidade": texto}, format="json"
    )


def incluir(client, agrupamento, emenda):
    return client.post(
        "/api/loa/agrupamentoemendaloa/",
        {"agrupamento": agrupamento.pk, "emendaloa": emenda.pk},
        format="json",
    )


@pytest.mark.spec("LOA-AGR-053")
def test_autosave_marca_finalidade_digitada_e_vazia_volta_ao_automatico(
    api, editor_contabil, agrupamento
):
    client = api(editor_contabil)

    digitar(client, agrupamento, "Digitada")
    agrupamento.refresh_from_db()
    assert (agrupamento.finalidade, agrupamento.finalidade_manual) == ("Digitada", True)

    digitar(client, agrupamento, "  ")
    agrupamento.refresh_from_db()
    assert agrupamento.finalidade_manual is False


@pytest.mark.spec("LOA-AGR-053")
def test_autosave_de_outro_campo_nao_marca_finalidade(
    api, editor_contabil, agrupamento
):
    api(editor_contabil).patch(
        f"/api/loa/agrupamento/{agrupamento.pk}/", {"nome": "Outro"}, format="json"
    )

    agrupamento.refresh_from_db()
    assert agrupamento.finalidade_manual is False


@pytest.mark.spec("LOA-AGR-053")
def test_inclusao_mantem_finalidade_digitada_sem_chamar_ia(
    ia_real, api, editor_contabil, com_emenda, make_emenda
):
    client = api(editor_contabil)
    digitar(client, com_emenda, "Digitada")

    with mock.patch(GERAR) as gerar:
        r = incluir(client, com_emenda, make_emenda(fase=EC))

    assert r.status_code == 201
    assert not gerar.called
    assert (r.data["agrupamento_finalidade"], r.data["aviso_finalidade"]) == (
        "Digitada",
        "",
    )


@pytest.mark.spec("LOA-AGR-053")
def test_inclusao_com_unidade_diferente_apaga_digitada_e_avisa(
    ia_real, api, editor_contabil, com_emenda, make_emenda, loa
):
    client = api(editor_contabil)
    digitar(client, com_emenda, "Digitada")
    outra_unidade = mommy.make(UnidadeOrcamentaria, loa=loa, codigo="02")

    r = incluir(client, com_emenda, make_emenda(fase=EC, unidade=outra_unidade))

    assert r.status_code == 201
    assert r.data["agrupamento_finalidade"] == ""
    assert r.data["aviso_finalidade"] == FinalidadeManualRemovida.MENSAGEM
    com_emenda.refresh_from_db()
    assert com_emenda.finalidade_manual is False


@pytest.mark.spec("LOA-AGR-053")
def test_inclusao_com_unidade_diferente_sem_digitada_nao_avisa(
    ia_real, api, editor_contabil, com_emenda, make_emenda, loa
):
    outra_unidade = mommy.make(UnidadeOrcamentaria, loa=loa, codigo="02")

    r = incluir(
        api(editor_contabil),
        com_emenda,
        make_emenda(fase=EC, unidade=outra_unidade),
    )

    assert r.data["agrupamento_finalidade"] == ""
    assert r.data["aviso_finalidade"] == ""


@pytest.mark.spec("LOA-AGR-053")
def test_ctrl_clique_substitui_digitada(ia_real, api, editor_contabil, com_emenda):
    client = api(editor_contabil)
    digitar(client, com_emenda, "Digitada")

    with mock.patch(GERAR, return_value="gerada"):
        r = client.patch(
            f"/api/loa/agrupamento/{com_emenda.pk}/generate_finalidade_global/"
        )

    assert r.json() == {"finalidade_global": "gerada"}
    com_emenda.refresh_from_db()
    assert (com_emenda.finalidade, com_emenda.finalidade_manual) == ("gerada", False)


@pytest.mark.spec("LOA-AGR-053")
def test_falha_da_ia_no_ctrl_clique_mantem_digitada(
    ia_real, api, editor_contabil, com_emenda
):
    client = api(editor_contabil)
    digitar(client, com_emenda, "Digitada")

    with mock.patch(GERAR, side_effect=IAEmentaEmendaColetivaError()):
        r = client.patch(
            f"/api/loa/agrupamento/{com_emenda.pk}/generate_finalidade_global/"
        )

    assert r.status_code == 400
    com_emenda.refresh_from_db()
    assert (com_emenda.finalidade, com_emenda.finalidade_manual) == ("Digitada", True)


# ------------------------------------------------- prévia exige permissão (D5)


def pdf_vazio(*args, **kwargs):
    import pymupdf

    doc = pymupdf.Document()
    doc.new_page()
    return doc.tobytes()


def get_previa(client, agrupamento):
    with mock.patch("cmj.api.loa.views.agrupamento.make_pdf", pdf_vazio):
        return client.get(f"/api/loa/agrupamento/{agrupamento.pk}/view/?model=1")


@pytest.fixture
def sem_finalidade(agrupamento, make_emenda):
    """Sem finalidade, a prévia pediria a finalidade automática à I.A."""
    agrupamento.finalidade = ""
    agrupamento.save()
    for _ in range(2):
        el = make_emenda(fase=EC, permite_juncao_coletiva=True)
        AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento, emendaloa=el)
    return agrupamento


@pytest.mark.spec("LOA-AGR-003")
@pytest.mark.parametrize("perfil", ["anonimo", "autor"])
def test_previa_recusa_quem_nao_edita_e_nao_chama_ia(
    request, client, perfil, sem_finalidade
):
    if perfil != "anonimo":
        client.force_login(request.getfixturevalue(perfil))

    with mock.patch(GERAR) as gerar:
        r = get_previa(client, sem_finalidade)

    assert r.status_code in (401, 403)
    assert not gerar.called


@pytest.mark.spec("LOA-AGR-003")
def test_previa_liberada_para_editor_contabil(client, editor_contabil, sem_finalidade):
    client.force_login(editor_contabil)

    with mock.patch(GERAR, return_value="gerada") as gerar:
        r = get_previa(client, sem_finalidade)

    assert r.status_code == 200
    assert r["Content-Type"] == "application/pdf"
    assert gerar.called


@pytest.mark.spec("LOA-AGR-002")
def test_detalhe_do_agrupamento_na_api_continua_publico(client, agrupamento):
    assert client.get(f"/api/loa/agrupamento/{agrupamento.pk}/").status_code == 200


# ------------------------------------- registros contábeis da emenda agrupada (D6)


@pytest.fixture
def agrupada(agrupamento_liberavel, make_emenda, parlamentar):
    """Emenda de R$ 1.000,00 num agrupamento com dedução e inserção de 100%.

    O parlamentar sustenta o valor: o sync() da emenda o recalcula pela soma deles.
    """
    el = make_emenda(fase=EC, parlamentar=parlamentar)
    AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento_liberavel, emendaloa=el)
    return el


def registros(emenda):
    return sorted(
        (r.despesa_id, r.valor)
        for r in EmendaLoaRegistroContabil.objects.filter(emendaloa=emenda)
    )


@pytest.mark.spec("LOA-AGR-046")
def test_remocao_mantem_registros_do_agrupamento_na_emenda(
    api, editor_contabil, agrupada, agrupamento_liberavel
):
    antes = registros(agrupada)
    assert [v for _, v in antes] == [Decimal("-1000.00"), Decimal("1000.00")]

    r = api(editor_contabil).post(
        "/api/loa/agrupamentoemendaloa/delete/",
        {"agrupamento": agrupamento_liberavel.pk, "emendaloa": agrupada.pk},
        format="json",
    )

    assert r.status_code == 200
    assert not AgrupamentoEmendaLoa.objects.filter(emendaloa=agrupada).exists()
    assert registros(agrupada) == antes


@pytest.mark.spec("LOA-AGR-045")
def test_emenda_agrupada_nao_exclui_registro_pela_emenda(
    api, editor_contabil, agrupada, agrupamento_liberavel
):
    registro = EmendaLoaRegistroContabil.objects.filter(emendaloa=agrupada).first()
    antes = registros(agrupada)

    r = api(editor_contabil).delete(
        f"/api/loa/emendaloaregistrocontabil/{registro.pk}/"
    )

    assert r.status_code == 400
    assert 'agrupamento "Agrupamento"' in str(r.data)
    assert registros(agrupada) == antes
    assert AgrupamentoEmendaLoa.objects.filter(emendaloa=agrupada).exists()


@pytest.mark.spec("LOA-AGR-045")
def test_emenda_agrupada_nao_inclui_registro_pela_emenda(
    api, editor_contabil, agrupada, loa
):
    despesa = mommy.make(Despesa, loa=loa)
    antes = registros(agrupada)

    r = api(editor_contabil).post(
        "/api/loa/emendaloaregistrocontabil/create_for_emendaloa_update/",
        {"emendaloa": agrupada.pk, "despesa": despesa.pk, "valor": "10,00"},
        format="json",
    )

    assert r.status_code == 400
    assert 'agrupamento "Agrupamento"' in str(r.data), r.data
    assert registros(agrupada) == antes


@pytest.mark.spec("LOA-AGR-045")
def test_emenda_agrupada_nao_altera_registro_pela_emenda(
    api, editor_contabil, agrupada
):
    registro = EmendaLoaRegistroContabil.objects.filter(emendaloa=agrupada).first()
    antes = registros(agrupada)

    r = api(editor_contabil).patch(
        f"/api/loa/emendaloaregistrocontabil/{registro.pk}/",
        {"valor": "1,00"},
        format="json",
    )

    assert r.status_code == 400
    assert 'agrupamento "Agrupamento"' in str(r.data), r.data
    assert registros(agrupada) == antes


@pytest.mark.spec("LOA-AGR-047")
def test_excluir_registro_da_emenda_nao_a_tira_do_agrupamento(agrupada):
    registro = EmendaLoaRegistroContabil.objects.filter(emendaloa=agrupada).first()

    registro.delete()

    assert AgrupamentoEmendaLoa.objects.filter(emendaloa=agrupada).exists()


# ------------------------------------------------------- erro do autosave (D4)


@pytest.mark.spec("LOA-AGR-064")
def test_autosave_com_nome_vazio_responde_400_e_nao_grava(
    api, editor_contabil, agrupamento
):
    r = api(editor_contabil).patch(
        f"/api/loa/agrupamento/{agrupamento.pk}/", {"nome": ""}, format="json"
    )

    assert r.status_code == 400
    assert "nome" in r.data
    agrupamento.refresh_from_db()
    assert agrupamento.nome == "Agrupamento"
