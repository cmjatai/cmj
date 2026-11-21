"""Dados globais das páginas do v8.

Reúne o que toda página precisa: o registro das zonas SPA, as preferências
guardadas em cookie, a regra de acesso usada por views e menu e o conteúdo de
``<script id="v8-global">``.

As funções recebem o usuário e valores simples. Nenhuma recebe a requisição.
"""

import hashlib
import json
from dataclasses import dataclass

from django.conf import settings
from django.urls import reverse
from image_cropping.utils import get_backend

# Exigências de acesso além das permissões do Django. O valor de SUPERUSUARIO
# não tem ponto, portanto nunca coincide com uma permissão ``app.codename``.
SUPERUSUARIO = "__superusuario__"
AUTENTICADO = "autenticado"

# Resultado de ``situacao_acesso``.
ACESSO_OK = "ok"
NAO_AUTENTICADO = "nao_autenticado"
SEM_PERMISSAO = "sem_permissao"

URL_BASE = "/v8/"
URL_FRAG = "/v8/_frag/"

# Cookies de preferência: nome, valores aceitos e valor padrão.
COOKIE_TEMA = "v8_tema"
COOKIE_SIDEBAR = "v8_sidebar"
TEMAS = ("claro", "escuro")
SIDEBARS = ("expandida", "recolhida")
SIDEBAR_PADRAO = "expandida"

_TAMANHO_AVATAR = (128, 128)


@dataclass(frozen=True)
class Zona:
    """Zona SPA: trecho de ``/v8/`` cujo miolo é do Vue Router."""

    nome: str
    prefixo: str
    titulo: str
    menu_ativo: str | None = None
    exige: object = None


# Cada zona é declarada uma única vez, aqui. As rotas Django e o JSON global
# saem deste registro.
ZONAS = {
    "demo-spa": Zona(
        "demo-spa", "demo/spa", "Demonstração SPA", "demo-spa", SUPERUSUARIO
    ),
}


def preferencias(cookies):
    """Lê tema e sidebar dos cookies, aceitando só os valores previstos.

    Valor fora da lista é descartado: o tema fica ``None`` (o CSS segue o
    sistema) e a sidebar volta ao padrão.
    """
    cookies = cookies or {}
    tema = cookies.get(COOKIE_TEMA)
    sidebar = cookies.get(COOKIE_SIDEBAR)
    return {
        "tema": tema if tema in TEMAS else None,
        "sidebar": sidebar if sidebar in SIDEBARS else SIDEBAR_PADRAO,
    }


def _autenticado(usuario):
    return bool(usuario is not None and usuario.is_authenticated)


def atende(usuario, exige):
    """Diz se o usuário cumpre a exigência.

    ``exige`` é ``None`` (todos, inclusive anônimo), ``AUTENTICADO``,
    ``SUPERUSUARIO``, uma permissão ou uma sequência de permissões em que basta
    uma.
    """
    if exige is None:
        return True
    if not _autenticado(usuario):
        return False
    if exige == AUTENTICADO:
        return True
    if exige == SUPERUSUARIO:
        return bool(usuario.is_active and usuario.is_superuser)
    if isinstance(exige, (tuple, list, set, frozenset)):
        return any(atende(usuario, uma) for uma in exige)
    return bool(usuario.has_perm(exige))


def situacao_acesso(usuario, exige):
    """Classifica o acesso: liberado, falta autenticar ou falta permissão."""
    if atende(usuario, exige):
        return ACESSO_OK
    if not _autenticado(usuario):
        return NAO_AUTENTICADO
    return SEM_PERMISSAO


def permissoes(usuario):
    """Lista ordenada das permissões do usuário. Anônimo não tem nenhuma."""
    if not _autenticado(usuario):
        return []
    return sorted(usuario.get_all_permissions())


def hash_permissoes(usuario):
    """Resumo do que decide o menu: ser superusuário e o conjunto de permissões.

    Usuários com as mesmas permissões têm o mesmo resumo, e qualquer mudança
    nelas produz outro. Anônimo equivale ao conjunto vazio.
    """
    superusuario = bool(_autenticado(usuario) and usuario.is_superuser)
    base = json.dumps([superusuario, permissoes(usuario)])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _identificador(usuario):
    """Nome de login sem o domínio.

    No PortalCMJ o nome de login é o e-mail do usuário, que não pode ir para o
    JSON global. Fica só o trecho antes do ``@``.
    """
    return str(usuario.get_username() or "").split("@", 1)[0]


def _avatar(usuario):
    """URL da miniatura do avatar, ou ``None`` se não houver ou se falhar."""
    try:
        avatar = getattr(usuario, "avatar", None)
        if not avatar:
            return None
        return get_backend().get_thumbnail_url(
            avatar,
            {
                "size": _TAMANHO_AVATAR,
                "box": usuario.cropping,
                "crop": True,
                "detail": True,
            },
        )
    except Exception:
        return None


def dados_usuario(usuario):
    """Dados de exibição do usuário: ``id``, ``username``, ``nome``, ``avatar``.

    Devolve ``None`` para anônimo. Não inclui e-mail nem outro dado pessoal.
    """
    if not _autenticado(usuario):
        return None
    # A miniatura consulta o banco. O resultado fica no próprio objeto, que
    # vive só durante a requisição, para a topbar e o JSON global dividirem.
    dados = getattr(usuario, "_v8_dados_usuario", None)
    if dados is None:
        identificador = _identificador(usuario)
        dados = {
            "id": usuario.pk,
            "username": identificador,
            "nome": usuario.get_full_name() or identificador,
            "avatar": _avatar(usuario),
        }
        usuario._v8_dados_usuario = dados
    return dict(dados)


def dados_globais(usuario, zona=None, preferencias=None):
    """Conteúdo de ``<script id="v8-global">``, com exatamente estas chaves."""
    preferencias = preferencias or {}
    tema = preferencias.get("tema")
    sidebar = preferencias.get("sidebar")
    return {
        "versao": settings.PORTALCMJ_VERSION,
        "debug": bool(settings.DEBUG),
        "autenticado": _autenticado(usuario),
        "usuario": dados_usuario(usuario),
        "permissoes": permissoes(usuario),
        "urls": {
            "api": "/api",
            "versao": "/api/version",
            "sessao": "/api/auth/session",
            "login": reverse("cmj.core:login"),
            "logout": reverse("cmj.core:logout"),
            "base": URL_BASE,
            "frag": URL_FRAG,
        },
        "zonas": {nome: URL_BASE + z.prefixo for nome, z in ZONAS.items()},
        "zona": zona if zona in ZONAS else None,
        "flags": {},
        "tema": tema if tema in TEMAS else None,
        "sidebar": sidebar if sidebar in SIDEBARS else SIDEBAR_PADRAO,
    }
