"""Erro da I.A. na finalidade do agrupamento (docs/specs/genia/ementa-emenda-coletiva.md)."""

from unittest import mock

import pytest

from cmj.loa.models import AgrupamentoEmendaLoa, EmendaLoa
from cmj.loa.models.m_agrupamento import Agrupamento
from cmj.utils.genia.loa_agrupamento import IAEmentaEmendaColetivaError

pytestmark = [pytest.mark.django_db, pytest.mark.spec("GENIA-LOA-002")]

MENSAGEM = IAEmentaEmendaColetivaError.MENSAGEM

# lido no import, antes do mock autouse do conftest
UPDATE_FINALIDADE_ORIGINAL = Agrupamento.update_finalidade_com_ia


@pytest.fixture
def ia_falha():
    with mock.patch(
        "cmj.loa.models.m_agrupamento.IAEmentaEmendaColetiva.gerar_finalidade_global",
        side_effect=IAEmentaEmendaColetivaError(),
    ) as m:
        yield m


@pytest.fixture
def ia_real():
    """Desfaz o mock de update_finalidade_com_ia do conftest."""
    with mock.patch.object(
        Agrupamento,
        "update_finalidade_com_ia",
        UPDATE_FINALIDADE_ORIGINAL,
    ):
        yield


@pytest.fixture
def agrupado(agrupamento, make_emenda, parlamentar):
    el = make_emenda(
        fase=EmendaLoa.EDICAO_CONTABIL,
        parlamentar=parlamentar,
        permite_juncao_coletiva=True,
    )
    AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento, emendaloa=el)
    return el


def test_update_finalidade_limpa_e_repassa_erro(
    ia_real, ia_falha, agrupamento, agrupado
):
    with pytest.raises(IAEmentaEmendaColetivaError):
        agrupamento.update_finalidade_com_ia()

    agrupamento.refresh_from_db()
    assert agrupamento.finalidade == ""


def test_geracao_manual_responde_400_com_mensagem(
    ia_real, ia_falha, api, editor_contabil, agrupamento, agrupado
):
    r = api(editor_contabil).patch(
        f"/api/loa/agrupamento/{agrupamento.pk}/generate_finalidade_global/"
    )

    assert r.status_code == 400
    assert r.json() == {"error": MENSAGEM}


def test_inclusao_conclui_e_avisa(
    ia_real, ia_falha, api, editor_contabil, agrupamento, make_emenda
):
    el = make_emenda(fase=EmendaLoa.PROPOSTA_LIBERADA)

    r = api(editor_contabil).post(
        "/api/loa/agrupamentoemendaloa/",
        {"agrupamento": agrupamento.pk, "emendaloa": el.pk},
        format="json",
    )

    assert r.status_code == 201
    assert r.data["aviso_finalidade"] == MENSAGEM
    assert r.data["agrupamento_finalidade"] == ""
    assert AgrupamentoEmendaLoa.objects.filter(emendaloa=el).exists()


def test_inclusao_sem_erro_devolve_finalidade_gerada(
    ia_real, api, editor_contabil, agrupamento, make_emenda
):
    el = make_emenda(fase=EmendaLoa.PROPOSTA_LIBERADA)

    with mock.patch(
        "cmj.loa.models.m_agrupamento.IAEmentaEmendaColetiva.gerar_finalidade_global",
        return_value="gerada",
    ):
        r = api(editor_contabil).post(
            "/api/loa/agrupamentoemendaloa/",
            {"agrupamento": agrupamento.pk, "emendaloa": el.pk},
            format="json",
        )

    assert r.data["aviso_finalidade"] == ""
    assert r.data["agrupamento_finalidade"] == "gerada"


def test_remocao_conclui_e_avisa(
    ia_real, ia_falha, api, editor_contabil, agrupamento, agrupado, make_emenda
):
    outra = make_emenda(fase=EmendaLoa.EDICAO_CONTABIL)
    AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento, emendaloa=outra)

    r = api(editor_contabil).post(
        "/api/loa/agrupamentoemendaloa/delete/",
        {"agrupamento": agrupamento.pk, "emendaloa": agrupado.pk},
        format="json",
    )

    assert r.status_code == 200
    assert r.data["aviso_finalidade"] == MENSAGEM
    assert not AgrupamentoEmendaLoa.objects.filter(emendaloa=agrupado).exists()


def test_remocao_gera_finalidade_sem_a_emenda_removida(
    ia_real, api, editor_contabil, agrupamento, agrupado, make_emenda
):
    outra = make_emenda(fase=EmendaLoa.EDICAO_CONTABIL, finalidade="fica")
    AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento, emendaloa=outra)

    with mock.patch("cmj.loa.models.m_agrupamento.IAEmentaEmendaColetiva") as ia_cls:
        ia_cls.return_value.gerar_finalidade_global.return_value = "gerada"
        api(editor_contabil).post(
            "/api/loa/agrupamentoemendaloa/delete/",
            {"agrupamento": agrupamento.pk, "emendaloa": agrupado.pk},
            format="json",
        )

    assert ia_cls.call_args.args == (["fica"],)


def test_previa_marca_aviso(ia_falha, agrupamento, agrupado):
    agrupamento.finalidade = ""
    agrupamento.save()

    dados = agrupamento.preparar_dados_para_coletiva(for_preview=True)

    assert dados[0]["aviso_finalidade"] == MENSAGEM
    assert dados[0]["finalidade_automatica"] == ""


def test_geracao_da_coletiva_interrompe_com_mensagem(
    ia_falha, api, editor_contabil, agrupamento, agrupado
):
    agrupamento.finalidade = ""
    agrupamento.save()

    r = api(editor_contabil).post(
        f"/api/loa/agrupamento/{agrupamento.pk}/gerar_emenda_coletiva/"
    )

    assert r.status_code == 400
    assert r.json() == {"error": MENSAGEM}
    assert recarregar_fase(agrupado) == EmendaLoa.EDICAO_CONTABIL


def recarregar_fase(emenda):
    return EmendaLoa.all_objects.all_objects().get(pk=emenda.pk).fase
