"""Consulta ao Google na validação do reCAPTCHA (cmj.mixins.recaptcha_confirmado)
e os formulários que a usam. Nenhum teste chama o Google."""

from types import SimpleNamespace
from unittest import mock

import pytest
from django import forms
from django.core.exceptions import ValidationError

from cmj.mixins import GoogleRecapthaFormMixin, recaptcha_confirmado
from cmj.ouvidoria.forms import DenunciaForm

pytestmark = [pytest.mark.django_db, pytest.mark.spec("LOA-PCT-069")]


def _google(resposta=None, erro=None):
    cliente = mock.Mock()
    if erro:
        cliente.request.side_effect = erro
    else:
        cliente.request.return_value = mock.Mock(data=resposta)
    return mock.patch("urllib3.PoolManager", return_value=cliente), cliente


def test_consulta_manda_a_chave_no_corpo_com_tempo_limite(settings):
    settings.GOOGLE_RECAPTCHA_SECRET_KEY = "chave-de-teste"
    trocado, cliente = _google(b'{"success": true}')

    with trocado:
        assert recaptcha_confirmado("token-do-usuario") is True

    (metodo, url), opcoes = cliente.request.call_args
    assert (metodo, url) == ("POST", "https://www.google.com/recaptcha/api/siteverify")
    assert "chave-de-teste" not in url and "token-do-usuario" not in url
    assert opcoes["fields"] == {
        "secret": "chave-de-teste",
        "response": "token-do-usuario",
    }
    assert opcoes["encode_multipart"] is False
    assert (opcoes["timeout"], opcoes["retries"]) == (5.0, False)


@pytest.mark.parametrize(
    "google",
    [
        {"erro": TimeoutError("sem resposta")},
        {"erro": OSError("sem rede")},
        {"resposta": b'{"success": false}'},
        {"resposta": b"resposta ilegivel"},
        {"resposta": b"[]"},
        {"resposta": b"{}"},
    ],
)
def test_qualquer_falha_conta_como_nao_confirmado(google):
    trocado, _ = _google(**google)

    with trocado:
        assert recaptcha_confirmado("token") is False


class _Formulario(GoogleRecapthaFormMixin, forms.Form):
    email = forms.EmailField()


def _formulario(dados):
    return _Formulario(data=dados, title_label="Título", action_label="Enviar")


def test_formulario_com_recaptcha_usa_a_mesma_consulta():
    dados = {"email": "alguem@exemplo.invalid", "g-recaptcha-response": "token"}

    trocado, cliente = _google(b'{"success": true}')
    with trocado:
        assert _formulario(dados).is_valid()
    assert cliente.request.call_args[1]["fields"]["response"] == "token"

    trocado, _ = _google(erro=TimeoutError("sem resposta"))
    with trocado:
        recusado = _formulario(dados)
        assert not recusado.is_valid()
    assert recusado.non_field_errors() == ["Ocorreu um erro na validação do reCAPTCHA."]

    sem_resposta = _formulario({"email": "alguem@exemplo.invalid"})
    assert not sem_resposta.is_valid()
    assert sem_resposta.non_field_errors() == ["Verificação do reCAPTCHA não efetuada."]


def test_formulario_de_denuncia_da_ouvidoria_usa_a_mesma_consulta():
    # o clean() só lê os dados enviados e os dados limpos
    denuncia = SimpleNamespace(
        cleaned_data={"descricao": "texto"}, data={"g-recaptcha-response": "token"}
    )

    trocado, cliente = _google(b'{"success": true}')
    with trocado:
        assert DenunciaForm.clean(denuncia) == {"descricao": "texto"}
    assert cliente.request.call_args[1]["timeout"] == 5.0

    trocado, _ = _google(b'{"success": false}')
    with trocado, pytest.raises(ValidationError):
        DenunciaForm.clean(denuncia)

    with pytest.raises(ValidationError):
        DenunciaForm.clean(SimpleNamespace(cleaned_data={}, data={}))
