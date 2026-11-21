"""Testes da spec docs/specs/v8/http.md, no que cabe ao Django.

Cada teste está ligado a uma regra pelo marker ``spec``.
"""

import json

import pytest
from django.test import RequestFactory

from cmj.v8 import views
from cmj.v8.services import s_demo, s_respostas
from cmj.v8.tests.conftest import (
    CABECALHOS_CLIENTE,
    CABECALHOS_FRAGMENTO,
    URL_DEMO_FRAGMENTO,
    URLS_DEMO_API,
    URLS_DEMO_PAGINAS,
    cliente_http,
)

pytestmark = pytest.mark.django_db

CHAVES_ERRO = {"detail", "errors", "non_field_errors"}


@pytest.mark.spec("V8-HTTP-004")
def test_toda_pagina_garante_o_cookie_csrftoken(comum, superusuario):
    # Inclusive páginas sem formulário e as de erro.
    casos = [
        (None, "/v8/", 200),
        (None, "/v8/nao-existe/", 404),
        (comum, "/v8/demo/clientes/", 403),
        (superusuario, "/v8/demo/spa/", 200),
        (superusuario, "/v8/demo/clientes/3/", 200),
    ]
    for usuario, url, status in casos:
        cliente = cliente_http(usuario)
        assert "csrftoken" not in cliente.cookies
        resposta = cliente.get(url)
        assert resposta.status_code == status, url
        assert resposta.cookies["csrftoken"].value, url


@pytest.mark.spec("V8-HTTP-013")
def test_erro_de_validacao_sai_com_400_e_corpo_padrao(superusuario):
    cliente = cliente_http(superusuario)

    def enviar(metodo, url, dados):
        return getattr(cliente, metodo)(
            url,
            data=dados if isinstance(dados, str) else json.dumps(dados),
            content_type="application/json",
            headers=CABECALHOS_CLIENTE,
        )

    invalido = {
        "nome": "Zé",
        "email": "ana.exemplo@exemplo.invalid",
        "cidade": "",
        "situacao": "inativo",
        "motivo": "",
    }
    for metodo, url in [
        ("post", "/v8/demo/api/clientes/"),
        ("put", "/v8/demo/api/clientes/5/"),
    ]:
        resposta = enviar(metodo, url, invalido)
        corpo = resposta.json()
        assert resposta.status_code == 400
        assert set(corpo) == CHAVES_ERRO
        assert corpo["detail"] == "Corrija os campos indicados."
        assert set(corpo["errors"]) == {"nome", "email", "cidade"}
        for mensagens in corpo["errors"].values():
            assert mensagens and all(isinstance(m, str) for m in mensagens)
        # Com erro de campo em "situacao" ou "motivo" ausente, a regra geral
        # ainda é avaliada.
        assert corpo["non_field_errors"] == [
            "Cliente inativo precisa de um motivo preenchido."
        ]

        # Corpo que não é um objeto JSON tem o mesmo formato.
        for ruim in ["{nao é json", "[1, 2]", '"texto"', ""]:
            resposta = enviar(metodo, url, ruim)
            corpo = resposta.json()
            assert resposta.status_code == 400
            assert set(corpo) == CHAVES_ERRO
            assert corpo["errors"] == {}
            assert len(corpo["non_field_errors"]) == 1


@pytest.mark.spec("V8-HTTP-013")
def test_corpo_de_erro_e_montado_por_uma_funcao_a_partir_do_form():
    form = s_demo.ClienteForm(
        {"nome": "", "email": "sem-arroba", "cidade": "Jataí", "situacao": "x"}
    )
    assert not form.is_valid()
    corpo = s_respostas.erro_validacao(form)
    assert set(corpo) == CHAVES_ERRO
    assert corpo["errors"] == {
        "nome": ["Informe o nome."],
        "email": ["Informe um e-mail válido."],
        "situacao": ["Situação inválida."],
    }
    assert corpo["non_field_errors"] == []
    # Serializável sem ajuda: só dict, list e str.
    assert json.loads(json.dumps(corpo)) == corpo

    valido = s_demo.ClienteForm(
        {
            "nome": "Nova Pessoa",
            "email": "nova@exemplo.invalid",
            "cidade": "Jataí",
            "situacao": "ativo",
        }
    )
    assert valido.is_valid()
    assert s_respostas.erro_validacao(valido) == {
        "detail": "Corrija os campos indicados.",
        "errors": {},
        "non_field_errors": [],
    }


@pytest.mark.spec("V8-HTTP-026")
def test_sem_autenticacao_o_cliente_recebe_401_e_a_navegacao_vai_ao_login():
    cliente = cliente_http()

    for url in URLS_DEMO_API + URLS_DEMO_PAGINAS + [URL_DEMO_FRAGMENTO]:
        for cabecalhos in (CABECALHOS_CLIENTE, CABECALHOS_FRAGMENTO):
            resposta = cliente.get(url, headers=cabecalhos)
            assert resposta.status_code == 401, url
            assert resposta.json() == s_respostas.nao_autenticado()
            assert resposta.json()["code"] == "nao_autenticado"
            assert resposta.json()["detail"]

    # Só o Accept de JSON, sem X-Requested-With, também é requisição do cliente.
    resposta = cliente.get(URL_DEMO_FRAGMENTO, headers={"Accept": "application/json"})
    assert resposta.status_code == 401

    # Navegação comum: redireciona ao login, com retorno para o que foi pedido.
    navegador = {"Accept": "text/html,application/xhtml+xml,application/json;q=0.9"}
    for url in URLS_DEMO_PAGINAS + [URL_DEMO_FRAGMENTO]:
        for cabecalhos in ({}, navegador):
            resposta = cliente.get(url + "?q=a b&pagina=2", headers=cabecalhos)
            assert resposta.status_code == 302, url
            assert (
                resposta["Location"] == f"/login/?next={url}%3Fq%3Da%2520b%26pagina%3D2"
            )

    # Endpoint JSON nunca redireciona.
    for url in URLS_DEMO_API:
        resposta = cliente.get(url, headers=navegador)
        assert resposta.status_code == 401, url
        assert resposta.json()["code"] == "nao_autenticado"


@pytest.mark.spec("V8-HTTP-026")
def test_requisicao_do_cliente_e_reconhecida_pelos_cabecalhos():
    fabrica = RequestFactory()
    casos = [
        ({}, False),
        ({"Accept": "text/html"}, False),
        ({"Accept": "*/*"}, False),
        ({"Accept": "text/html,application/json"}, False),
        ({"Accept": "application/json"}, True),
        ({"Accept": "application/json, text/plain, */*"}, True),
        ({"X-Requested-With": "XMLHttpRequest"}, True),
        ({"X-Requested-With": "XMLHttpRequest", "Accept": "text/html"}, True),
        ({"X-Requested-With": "outro"}, False),
    ]
    for cabecalhos, esperado in casos:
        request = fabrica.get("/v8/", headers=cabecalhos)
        assert views.requisicao_do_cliente(request) is esperado, cabecalhos
