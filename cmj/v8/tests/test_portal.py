"""Testes da spec docs/specs/v8/portal.md.

Cada teste está ligado a uma regra pelo marker ``spec``.
"""

from unittest import mock

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core import signing
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import resolve, reverse
from django.urls.base import set_urlconf

import cmj.urls
from cmj.sigad.views import PaginaInicialView
from cmj.v8 import urls_raiz, views
from cmj.v8.middleware import PortalV8Middleware
from cmj.v8.services import s_portal
from cmj.v8.tests.conftest import (
    DIR_TEMPLATES_V8,
    cliente_http,
    html_de,
    renderizar,
)

pytestmark = pytest.mark.django_db

URL_ATIVAR = "/v8/portal/ativar/"
URL_DESATIVAR = "/v8/portal/desativar/"
PAGINA_INICIAL_V2018 = (
    DIR_TEMPLATES_V8.parent / "v2018" / "path" / "pagina_inicial.html"
)


def cookie_valido(usuario):
    return s_portal.cookie_ativar(usuario)["value"]


def passar_pelo_middleware(cookies=None):
    """Requisição a ``/`` depois do middleware, sem chegar a view nenhuma."""
    request = RequestFactory().get("/")
    request.COOKIES.update(cookies or {})
    PortalV8Middleware(lambda r: HttpResponse())(request)
    return request


def resolver_no_modo(caminho, urlconf):
    return resolve(caminho, urlconf=urlconf)


@pytest.fixture(autouse=True)
def _urlconf_padrao():
    """O middleware muda o urlconf da thread; cada teste começa e termina no padrão."""
    set_urlconf(None)
    yield
    set_urlconf(None)


# --- Escolha das rotas -------------------------------------------------------


@pytest.mark.spec("V8-PORTAL-001", "V8-PORTAL-011")
def test_sem_cookie_valido_a_requisicao_usa_as_rotas_de_sempre(superusuario):
    adulterado = cookie_valido(superusuario)[:-1] + "x"
    for cookies in (
        {},
        {s_portal.COOKIE_PORTAL: ""},
        {s_portal.COOKIE_PORTAL: "1"},
        {s_portal.COOKIE_PORTAL: adulterado},
        {s_portal.COOKIE_PORTAL: signing.TimestampSigner(salt="outro").sign("1")},
    ):
        request = passar_pelo_middleware(cookies)
        assert not hasattr(request, "urlconf"), cookies
        assert not hasattr(request, "v8_portal"), cookies

    assert resolve("/").func.view_class is PaginaInicialView


@pytest.mark.spec("V8-PORTAL-001")
def test_middleware_vem_depois_da_autenticacao():
    middlewares = list(settings.MIDDLEWARE)
    assert middlewares.index("cmj.v8.middleware.PortalV8Middleware") == (
        middlewares.index("django.contrib.auth.middleware.AuthenticationMiddleware") + 1
    )


@pytest.mark.spec("V8-PORTAL-002")
def test_com_cookie_valido_a_raiz_abre_a_pagina_inicial_do_v8(superusuario):
    request = passar_pelo_middleware(
        {s_portal.COOKIE_PORTAL: cookie_valido(superusuario)}
    )
    assert request.urlconf == s_portal.URLCONF_RAIZ
    assert request.v8_portal is True
    assert resolver_no_modo("/", urls_raiz).func.view_class is views.InicioView

    cliente = cliente_http()
    cliente.cookies[s_portal.COOKIE_PORTAL] = cookie_valido(superusuario)
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "v8/paginas/inicio.html" in [t.name for t in resposta.templates]
    assert 'data-v8-layout="landing"' in html_de(resposta)


@pytest.mark.spec("V8-PORTAL-002")
def test_com_cookie_valido_os_outros_caminhos_resolvem_para_as_mesmas_views():
    for caminho in (
        "/materia/1",
        "/norma/1",
        "/sessao/1",
        "/v8/",
        "/v8/ds/",
        "/api/materia/materialegislativa/",
        "/qualquer/pagina/do/portal",
    ):
        padrao = resolver_no_modo(caminho, cmj.urls)
        raiz = resolver_no_modo(caminho, urls_raiz)
        assert raiz.func == padrao.func, caminho
        assert raiz.view_name == padrao.view_name, caminho

    for nome in ("cmj.sigad:pagina_inicial_view", "cmj.v8:inicio", "cmj.v8:ds"):
        assert reverse(nome, urlconf=urls_raiz) == reverse(nome, urlconf=cmj.urls)
    assert reverse("cmj.sigad:pagina_inicial_view", urlconf=urls_raiz) == "/"


# --- Cookie ------------------------------------------------------------------


@pytest.mark.spec("V8-PORTAL-003")
def test_cookie_assinado_com_validade_de_doze_horas(superusuario, settings):
    settings.DEBUG = False
    cookie = s_portal.cookie_ativar(superusuario)
    assert cookie["key"] == "v8_portal"
    assert cookie["path"] == "/"
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"
    assert cookie["secure"] is True
    assert cookie["max_age"] == s_portal.VALIDADE == 12 * 60 * 60
    assert signing.TimestampSigner(salt=s_portal.SALT).unsign(cookie["value"]) == str(
        superusuario.pk
    )
    assert s_portal.ativo(cookie["value"])


@pytest.mark.spec("V8-PORTAL-003")
def test_cookie_adulterado_sem_assinatura_ou_vencido_nao_vale(superusuario):
    valor = cookie_valido(superusuario)
    assert not s_portal.ativo(None)
    assert not s_portal.ativo("")
    assert not s_portal.ativo(str(superusuario.pk))
    assert not s_portal.ativo(valor[:-1] + ("x" if valor[-1] != "x" else "y"))
    assert not s_portal.ativo(signing.TimestampSigner(salt="outro").sign("1"))

    # Assinado agora; lido 12 h e 1 s depois.
    with mock.patch("time.time", return_value=signing.time.time() + 12 * 3600 + 1):
        assert not s_portal.ativo(valor)
    with mock.patch("time.time", return_value=signing.time.time() + 12 * 3600 - 60):
        assert s_portal.ativo(valor)


@pytest.mark.spec("V8-PORTAL-003")
def test_cookie_continua_valendo_depois_do_logout(superusuario):
    cliente = cliente_http(superusuario)
    resposta = cliente.post(URL_ATIVAR, {"next": "/"})
    assert resposta.status_code == 302
    # Logout pela rota do portal: o Client.logout() do Django apagaria todos os cookies.
    cliente.post(reverse("cmj.core:logout"))
    assert "_auth_user_id" not in cliente.session
    assert s_portal.ativo(cliente.cookies[s_portal.COOKIE_PORTAL].value)

    resposta = cliente.get("/")
    assert "v8/paginas/inicio.html" in [t.name for t in resposta.templates]


# --- Ativar e desativar ------------------------------------------------------


@pytest.mark.spec("V8-PORTAL-004")
def test_so_superusuario_liga_o_v8(comum, superusuario):
    assert not s_portal.pode_ativar(None)
    assert not s_portal.pode_ativar(AnonymousUser())
    assert not s_portal.pode_ativar(comum)
    assert s_portal.pode_ativar(superusuario)
    assert s_portal.cookie_ativar(AnonymousUser()) is None
    assert s_portal.cookie_ativar(comum) is None

    resposta = cliente_http().post(URL_ATIVAR, {"next": "/"})
    assert resposta.status_code == 302
    assert resposta["Location"].startswith(reverse("cmj.core:login"))
    assert s_portal.COOKIE_PORTAL not in resposta.cookies

    resposta = cliente_http(comum).post(URL_ATIVAR, {"next": "/"})
    assert resposta.status_code == 403
    assert s_portal.COOKIE_PORTAL not in resposta.cookies


@pytest.mark.spec("V8-PORTAL-004")
def test_superusuario_recebe_o_cookie_e_volta_ao_destino(superusuario):
    resposta = cliente_http(superusuario).post(URL_ATIVAR, {"next": "/materia/1"})
    assert resposta.status_code == 302
    assert resposta["Location"] == "/materia/1"
    morsel = resposta.cookies[s_portal.COOKIE_PORTAL]
    assert morsel["path"] == "/"
    assert morsel["httponly"]
    assert morsel["samesite"] == "Lax"
    assert s_portal.ativo(morsel.value)

    resposta = cliente_http(superusuario).post(URL_ATIVAR)
    assert resposta["Location"] == "/"


@pytest.mark.spec("V8-PORTAL-004", "V8-PORTAL-011")
def test_ativar_aceita_so_post_com_csrf(superusuario):
    cliente = cliente_http(superusuario, enforce_csrf_checks=True)
    for metodo in ("get", "head"):
        assert getattr(cliente, metodo)(URL_ATIVAR).status_code == 405, metodo
    # PUT e DELETE sem token são barrados já pelo CSRF.
    for metodo in ("put", "delete"):
        resposta = getattr(cliente, metodo)(URL_ATIVAR)
        assert resposta.status_code in (403, 405), metodo
        assert s_portal.COOKIE_PORTAL not in resposta.cookies, metodo
    resposta = cliente.post(URL_ATIVAR, {"next": "/"})
    assert resposta.status_code == 403
    assert s_portal.COOKIE_PORTAL not in resposta.cookies


@pytest.mark.spec("V8-PORTAL-005")
def test_qualquer_pessoa_desliga_o_v8(superusuario):
    cliente = cliente_http()
    cliente.cookies[s_portal.COOKIE_PORTAL] = cookie_valido(superusuario)
    resposta = cliente.post(URL_DESATIVAR, {"next": "/"})
    assert resposta.status_code == 302
    assert resposta["Location"] == "/"
    morsel = resposta.cookies[s_portal.COOKIE_PORTAL]
    assert morsel.value == ""
    assert morsel["path"] == "/"
    assert morsel["max-age"] == 0


@pytest.mark.spec("V8-PORTAL-005", "V8-PORTAL-011")
def test_desativar_aceita_so_post_com_csrf(superusuario):
    cliente = cliente_http(enforce_csrf_checks=True)
    cliente.cookies[s_portal.COOKIE_PORTAL] = cookie_valido(superusuario)
    for metodo in ("get", "head"):
        assert getattr(cliente, metodo)(URL_DESATIVAR).status_code == 405, metodo
    # PUT e DELETE sem token são barrados já pelo CSRF.
    for metodo in ("put", "delete"):
        resposta = getattr(cliente, metodo)(URL_DESATIVAR)
        assert resposta.status_code in (403, 405), metodo
        assert s_portal.COOKIE_PORTAL not in resposta.cookies, metodo
    resposta = cliente.post(URL_DESATIVAR, {"next": "/"})
    assert resposta.status_code == 403
    assert s_portal.COOKIE_PORTAL not in resposta.cookies


@pytest.mark.spec("V8-PORTAL-006")
def test_destino_so_aceita_caminho_do_mesmo_host(superusuario):
    host = "testserver"
    for aceito in ("/", "/materia/1", "/norma/?ano=2025"):
        assert s_portal.destino(aceito, host) == aceito
    for recusado in (
        None,
        "",
        "materia/1",
        "http://outro.example/",
        "https://testserver/",
        "//outro.example/",
        "/\\outro.example/",
        "javascript:alert(1)",
        " /materia/1",
    ):
        assert s_portal.destino(recusado, host) == "/", recusado

    resposta = cliente_http(superusuario).post(URL_ATIVAR, {"next": "//outro.example/"})
    assert resposta["Location"] == "/"
    resposta = cliente_http().post(URL_DESATIVAR, {"next": "http://outro.example/"})
    assert resposta["Location"] == "/"


# --- Botões ------------------------------------------------------------------


@pytest.mark.spec("V8-PORTAL-007")
def test_botao_de_ligar_so_aparece_para_superusuario(comum, superusuario):
    fonte = '{% include "v8/partials/portal/ativar_v2018.html" %}'
    assert 'data-v8-portal="ativar"' not in renderizar(fonte, caminho="/")
    assert 'data-v8-portal="ativar"' not in renderizar(fonte, comum, caminho="/")
    html = renderizar(fonte, superusuario, caminho="/")
    assert 'data-v8-portal="ativar"' in html
    assert f'action="{URL_ATIVAR}"' in html
    assert 'name="csrfmiddlewaretoken"' in html


@pytest.mark.spec("V8-PORTAL-007")
def test_pagina_inicial_do_v2018_inclui_o_botao_fora_do_cache():
    fonte = PAGINA_INICIAL_V2018.read_text()
    inclusao = '{% include "v8/partials/portal/ativar_v2018.html" %}'
    assert fonte.count(inclusao) == 1
    antes = fonte[: fonte.index(inclusao)]
    assert antes.count("{% cache") == antes.count("{% endcache %}")


@pytest.mark.spec("V8-PORTAL-008")
def test_botao_de_voltar_so_aparece_com_o_v8_ligado(superusuario):
    pagina = '{% extends "v8/layouts/landing.html" %}'
    assert 'data-v8-portal="voltar"' not in renderizar(pagina)

    cliente = cliente_http()
    assert 'data-v8-portal="voltar"' not in html_de(cliente.get("/v8/"))
    cliente.cookies[s_portal.COOKIE_PORTAL] = cookie_valido(superusuario)
    for caminho in ("/", "/v8/"):
        html = html_de(cliente.get(caminho))
        assert 'data-v8-portal="voltar"' in html, caminho
        assert f'action="{URL_DESATIVAR}"' in html, caminho
        assert f'name="next" value="{caminho}"' in html, caminho


# --- Rotas da raiz -----------------------------------------------------------


@pytest.mark.spec("V8-PORTAL-009")
def test_rotas_da_raiz_usam_o_mesmo_handler403():
    assert urls_raiz.handler403 is cmj.urls.handler403


# --- Segurança ---------------------------------------------------------------


@pytest.mark.spec("V8-PORTAL-010")
def test_cookie_nao_da_permissao_e_a_pagina_continua_privada(comum, superusuario):
    cliente = cliente_http(comum)
    cliente.cookies[s_portal.COOKIE_PORTAL] = cookie_valido(superusuario)
    # Rota do v8 que exige superusuário continua recusada.
    assert cliente.get("/v8/demo/spa/").status_code == 403
    assert cliente.post(URL_ATIVAR).status_code == 403

    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "private" in resposta["Cache-Control"]


@pytest.mark.spec("V8-PORTAL-010")
def test_servico_nao_recebe_a_requisicao():
    import inspect

    for nome, funcao in inspect.getmembers(s_portal, inspect.isfunction):
        if funcao.__module__ == s_portal.__name__:
            assert "request" not in inspect.signature(funcao).parameters, nome
