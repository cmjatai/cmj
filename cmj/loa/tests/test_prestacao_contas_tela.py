"""Tela de prestação de contas da LOA (`/loa/<pk>/prestacaoconta`): conferência
da LOA na tela, no gate do reCAPTCHA e no relatório."""

import datetime
from unittest import mock

import pytest
from django.test import override_settings
from model_bakery import baker as mommy

from cmj.loa.models import Loa
from cmj.mixins import GoogleRecapthaViewMixin
from sapl.materia.models import MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Legislatura

pytestmark = [pytest.mark.django_db]


@pytest.fixture(autouse=True)
def legislatura_atual(db):
    return Legislatura.objects.create(
        numero=99,
        data_inicio=datetime.date(2025, 1, 1),
        data_fim=datetime.date(2028, 12, 31),
        data_eleicao=datetime.date(2024, 10, 6),
    )


def _loa(ano, publicado, com_norma):
    materia = mommy.make(
        MateriaLegislativa,
        numero=ano,
        ano=ano - 1,
        data_apresentacao=datetime.date(ano - 1, 9, 1),
    )
    if com_norma:
        mommy.make(NormaJuridica, materia=materia)
    return mommy.make(Loa, ano=ano, publicado=publicado, materia=materia)


def _acessos(client, pk):
    """Status da tela, do gate do reCAPTCHA e do relatório."""
    url = f"/loa/{pk}/prestacaoconta"
    tela = client.get(url)
    gate = client.get(f"{url}?print=True")
    with mock.patch.object(
        GoogleRecapthaViewMixin, "_validate_recaptcha", return_value=True
    ):
        relatorio = client.post(f"{url}?print=True", {"g-recaptcha-response": "token"})
    return tela, gate, relatorio


def _status(respostas):
    return [r.status_code for r in respostas]


@pytest.mark.spec("LOA-PCT-064")
def test_loa_publicada_com_norma_abre_tela_gate_e_relatorio(client):
    loa = _loa(2091, publicado=True, com_norma=True)

    tela, gate, relatorio = _acessos(client, loa.pk)

    assert _status((tela, gate, relatorio)) == [200, 200, 200]
    assert "recaptcha" in gate.content.decode().lower()
    assert str(loa.ano) in relatorio.content.decode()


@pytest.mark.spec("LOA-PCT-064")
@pytest.mark.parametrize("perfil", ["anonimo", "comum"])
def test_loa_nao_publicada_responde_404_em_tela_gate_e_relatorio(
    client, django_user_model, perfil
):
    loa = _loa(2092, publicado=False, com_norma=True)
    if perfil == "comum":
        client.force_login(
            django_user_model.objects.create_user(
                email="comum@test.local", password="testpass123!"
            )
        )

    assert _status(_acessos(client, loa.pk)) == [404, 404, 404]


@pytest.mark.spec("LOA-PCT-064")
def test_loa_inexistente_responde_404_em_tela_gate_e_relatorio(client):
    assert _status(_acessos(client, 999999)) == [404, 404, 404]


@pytest.mark.spec("LOA-PCT-064")
def test_loa_sem_norma_leva_ao_detalhe_da_loa_em_tela_gate_e_relatorio(client):
    loa = _loa(2093, publicado=True, com_norma=False)

    respostas = _acessos(client, loa.pk)

    assert _status(respostas) == [302, 302, 302]
    assert {r["Location"] for r in respostas} == {f"/loa/{loa.pk}"}


@pytest.mark.spec("LOA-PCT-064")
def test_editor_da_contabilidade_ve_loa_nao_publicada(client, editor_contabil):
    loa = _loa(2094, publicado=False, com_norma=True)
    client.force_login(editor_contabil)

    assert _status(_acessos(client, loa.pk)) == [200, 200, 200]


@pytest.mark.spec("LOA-PCT-064")
def test_operador_de_autor_segue_a_visibilidade_da_loa(client, autor):
    # a LOA não publicada cuja matéria virou norma some para ele; a que ainda
    # não virou norma ele vê, mas a prestação de contas leva ao detalhe da LOA
    virou_norma = _loa(2095, publicado=False, com_norma=True)
    sem_norma = _loa(2096, publicado=False, com_norma=False)
    client.force_login(autor)

    assert _status(_acessos(client, virou_norma.pk)) == [404, 404, 404]
    assert _status(_acessos(client, sem_norma.pk)) == [302, 302, 302]


@pytest.mark.spec("LOA-PCT-065")
def test_em_desenvolvimento_o_relatorio_dispensa_o_recaptcha(client):
    loa = _loa(2097, publicado=True, com_norma=True)
    url = f"/loa/{loa.pk}/prestacaoconta?print=True"

    gate = client.get(url).content.decode()
    assert "recaptcha" in gate.lower()

    with override_settings(DEBUG=True):
        direto = client.get(url)

    assert direto.status_code == 200
    html = direto.content.decode()
    assert "Prestação de Contas das Emendas Impositivas" in html
    assert "g-recaptcha" not in html


@pytest.mark.spec("LOA-PCT-065")
def test_em_desenvolvimento_a_conferencia_da_loa_continua_valendo(client):
    nao_publicada = _loa(2098, publicado=False, com_norma=True)

    with override_settings(DEBUG=True):
        resposta = client.get(f"/loa/{nao_publicada.pk}/prestacaoconta?print=True")

    assert resposta.status_code == 404


@pytest.mark.spec("LOA-PCT-007")
def test_loa_atual_leva_a_loa_publicada_mais_recente_com_emendas(
    client, loa, make_emenda
):
    assert client.get("/loa/atual").status_code == 404

    make_emenda()
    _loa(2099, publicado=True, com_norma=True)  # mais recente, mas sem emendas

    resposta = client.get("/loa/atual")
    assert resposta.status_code == 302
    assert resposta["Location"] == f"/loa/{loa.pk}/prestacaoconta"

    # a LOA do atalho ainda não virou norma: a prestação de contas leva ao detalhe dela
    seguinte = client.get(resposta["Location"])
    assert (seguinte.status_code, seguinte["Location"]) == (302, f"/loa/{loa.pk}")


@pytest.mark.spec("LOA-PCT-068")
def test_retornar_do_gate_volta_a_prestacao_de_contas_com_os_filtros(client):
    loa = _loa(2096, publicado=True, com_norma=True)
    url = f"/loa/{loa.pk}/prestacaoconta"

    gate = client.get(f"{url}?view=list&situacao=IMPEDIMENTO&print=True")
    assert f'href="{url}?view=list&amp;situacao=IMPEDIMENTO"' in gate.content.decode()

    sem_filtros = client.get(f"{url}?print=True").content.decode()
    assert f'<a href="{url}" class="btn btn-secondary">' in sem_filtros


def _google(resposta=None, erro=None):
    """Troca o cliente HTTP da validação do reCAPTCHA: nenhum teste chama o
    Google."""
    cliente = mock.Mock()
    if erro:
        cliente.request.side_effect = erro
    else:
        cliente.request.return_value = mock.Mock(data=resposta)
    return mock.patch("urllib3.PoolManager", return_value=cliente), cliente


@pytest.mark.spec("LOA-PCT-069")
def test_validacao_do_recaptcha_manda_a_chave_no_corpo_com_tempo_limite(
    client, settings
):
    settings.GOOGLE_RECAPTCHA_SECRET_KEY = "chave-de-teste"
    loa = _loa(2095, publicado=True, com_norma=True)
    trocado, cliente = _google(b'{"success": true}')

    with trocado:
        resposta = client.post(
            f"/loa/{loa.pk}/prestacaoconta?print=True",
            {"g-recaptcha-response": "token-do-usuario"},
        )

    assert resposta.status_code == 200
    assert "Prestação de Contas das Emendas Impositivas" in resposta.content.decode()
    (metodo, url), opcoes = cliente.request.call_args
    assert (metodo, url) == ("POST", "https://www.google.com/recaptcha/api/siteverify")
    assert opcoes["fields"] == {
        "secret": "chave-de-teste",
        "response": "token-do-usuario",
    }
    assert opcoes["encode_multipart"] is False
    assert (opcoes["timeout"], opcoes["retries"]) == (5.0, False)


@pytest.mark.spec("LOA-PCT-069")
@pytest.mark.parametrize(
    "google",
    [
        {"erro": TimeoutError("sem resposta")},
        {"resposta": b'{"success": false}'},
        {"resposta": b"resposta ilegivel"},
        {"resposta": b"[]"},
    ],
)
def test_recaptcha_sem_resposta_valida_volta_ao_gate_com_erro(client, google):
    loa = _loa(2094, publicado=True, com_norma=True)
    trocado, _ = _google(**google)

    with trocado:
        resposta = client.post(
            f"/loa/{loa.pk}/prestacaoconta?print=True",
            {"g-recaptcha-response": "token"},
        )

    html = resposta.content.decode()
    assert resposta.status_code == 200
    assert "Ocorreu um erro na validação do reCAPTCHA." in html
    assert "g-recaptcha" in html


@pytest.mark.spec("LOA-PCT-070")
def test_titulo_do_relatorio_exibe_o_nome_da_loa_como_texto(client):
    loa = _loa(2093, publicado=True, com_norma=True)
    marcacao = '<b id="marcador">X</b>'
    norma = NormaJuridica.objects.get(materia=loa.materia)
    type(norma.tipo).objects.filter(pk=norma.tipo_id).update(descricao=marcacao)
    assert marcacao in str(Loa.objects.get(pk=loa.pk))

    with override_settings(DEBUG=True):
        html = client.get(f"/loa/{loa.pk}/prestacaoconta?print=True").content.decode()

    assert marcacao not in html
    assert "&lt;b id=&quot;marcador&quot;&gt;X&lt;/b&gt;" in html
    # a quebra de linha do título continua sendo marcação
    assert "Prestação de Contas das Emendas Impositivas <br>LOA 2093" in html
