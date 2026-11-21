"""Fixtures e auxiliares dos testes do v8 (docs/specs/v8).

Perfis usados: anônimo, usuário comum (autenticado, sem permissões) e
superusuário.
"""

import json
import re

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

CACHE_REAL = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "v8-test",
    }
}

# Cabeçalhos que o cliente HTTP do frontend envia em toda requisição.
CABECALHOS_CLIENTE = {
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json",
}
CABECALHOS_FRAGMENTO = {
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "text/html",
}

URLS_DEMO_PAGINAS = [
    "/v8/demo/clientes/",
    "/v8/demo/clientes/1/",
    "/v8/demo/spa/",
    "/v8/demo/spa/clientes/1",
]
URLS_DEMO_API = [
    "/v8/demo/api/clientes/",
    "/v8/demo/api/clientes/1/",
    "/v8/demo/api/negado/",
]
URL_DEMO_FRAGMENTO = "/v8/_frag/demo/cliente/1/historico/"


def criar_usuario(nome, superusuario=False, **campos):
    usuario = get_user_model().objects.create_user(
        email=f"{nome}@teste.local", password="senha-de-teste-123!"
    )
    usuario.is_superuser = superusuario
    usuario.is_staff = superusuario
    for campo, valor in campos.items():
        setattr(usuario, campo, valor)
    usuario.save()
    # Recarrega para não levar o cache de permissões do objeto.
    return get_user_model().objects.get(pk=usuario.pk)


def cliente_http(usuario=None, **opcoes):
    cliente = Client(**opcoes)
    if usuario is not None:
        cliente.force_login(usuario)
    return cliente


def html_de(resposta):
    return resposta.content.decode("utf-8")


def ler_json_script(html, id_script):
    """Conteúdo de ``<script id="..." type="application/json">`` já convertido."""
    achado = re.search(
        rf'<script id="{re.escape(id_script)}" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    assert achado, f"script #{id_script} ausente"
    return json.loads(achado.group(1))


def trecho(html, inicio, fim):
    """Parte do HTML entre dois marcadores, incluindo-os."""
    a = html.index(inicio)
    b = html.index(fim, a) + len(fim)
    return html[a:b]


@pytest.fixture
def comum(db):
    return criar_usuario("comum", first_name="Maria", last_name="Comum")


@pytest.fixture
def superusuario(db):
    return criar_usuario(
        "super", superusuario=True, first_name="Sofia", last_name="Super"
    )


@pytest.fixture
def cache_real(settings):
    """Troca o DummyCache dos testes por um cache em memória, limpo antes e depois."""
    from django.core.cache import cache

    settings.CACHES = CACHE_REAL
    cache.clear()
    yield cache
    cache.clear()
