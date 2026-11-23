"""Fixtures e auxiliares dos testes do v8 (docs/specs/v8).

Perfis usados: anônimo, usuário comum (autenticado, sem permissões) e
superusuário.
"""

import json
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.template import engines
from django.test import Client, RequestFactory

DIR_TEMPLATES_V8 = next(
    Path(d) for d in settings.TEMPLATES[0]["DIRS"] if Path(d).name == "v8"
)
DIR_CSS_V8 = Path(settings.PROJECT_DIR_FRONTEND_V8) / "src" / "css"
DIR_CSS_OFICIAL = DIR_CSS_V8 / "temas" / "oficial"

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

URLS_DEMO_LAYOUTS = [
    "/v8/demo/layouts/landing/",
    "/v8/demo/layouts/app_topbar/",
    "/v8/demo/layouts/app_sidebar/",
    "/v8/demo/layouts/minimal/",
]
URLS_DEMO_PAGINAS = [
    "/v8/demo/clientes/",
    "/v8/demo/clientes/1/",
    "/v8/demo/spa/",
    "/v8/demo/spa/clientes/1",
    *URLS_DEMO_LAYOUTS,
]
URLS_DEMO_API = [
    "/v8/demo/api/clientes/",
    "/v8/demo/api/clientes/1/",
    "/v8/demo/api/negado/",
]
URL_DEMO_FRAGMENTO = "/v8/_frag/demo/cliente/1/historico/"
# Páginas do design system: a vitrine, a lista de temas e a prévia de cada tema.
URLS_DS = [
    "/v8/ds/",
    "/v8/ds/temas/",
    "/v8/ds/temas/oficial/",
    "/v8/ds/temas/verde/",
    "/v8/ds/temas/terracota/",
    "/v8/ds/temas/contraste/",
]


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


def templates_v8():
    """Todos os arquivos de ``_templates/v8``."""
    return sorted(p for p in DIR_TEMPLATES_V8.rglob("*") if p.is_file())


def renderizar(fonte, usuario=None, contexto=None, caminho="/v8/", cookies=None):
    """Renderiza um template escrito no teste, como uma view faria com ``render``."""
    request = RequestFactory().get(caminho)
    request.user = usuario or AnonymousUser()
    request.COOKIES.update(cookies or {})
    return engines["django"].from_string(fonte).render(contexto or {}, request)


def pagina_no_layout(layout, blocos="", **opcoes):
    """Uma página mínima que estende o layout e acrescenta os blocks informados."""
    return renderizar(f'{{% extends "v8/layouts/{layout}.html" %}}{blocos}', **opcoes)


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
