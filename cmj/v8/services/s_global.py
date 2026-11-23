"""Dados globais das páginas do v8.

Reúne o que toda página precisa: o registro das zonas SPA e dos temas, as
preferências guardadas em cookie, a regra de acesso usada por views e menu e o conteúdo de
``<script id="v8-global">``.

As funções recebem o usuário e valores simples. Nenhuma recebe a requisição.
"""

import hashlib
import json
import re
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
COOKIE_MODO = "v8_modo"
COOKIE_SIDEBAR = "v8_sidebar"
COOKIE_TEMA = "v8_tema"
MODOS = ("claro", "escuro")
SIDEBARS = ("expandida", "recolhida")
SIDEBAR_PADRAO = "expandida"

# Validade do cookie de tema, em segundos: um ano, como os gravados pelo navegador.
_IDADE_COOKIE = 365 * 24 * 60 * 60

# Temas (docs/specs/v8/temas.md): o design do v8. Modo é claro ou escuro, e todo
# tema tem os dois. O nome é o da pasta em ``_frontend/v8/src/css/temas/`` e o
# valor de ``<html data-tema>``.
TEMA_PADRAO = "oficial"
_NOME_DE_TEMA = re.compile(r"[a-z][a-z0-9-]*")


def validar_temas(temas):
    """Confere o registro de temas e o devolve.

    O padrão vem primeiro, e cada nome tem só minúsculas, dígitos e hífen,
    começa por letra e não é o nome de um modo. Outro registro é erro na carga
    do projeto.
    """
    nomes = list(temas)
    if not nomes or nomes[0] != TEMA_PADRAO:
        raise ValueError(f"O primeiro tema do registro deve ser {TEMA_PADRAO}.")
    for nome in nomes:
        if not _NOME_DE_TEMA.fullmatch(nome) or nome in MODOS:
            raise ValueError(f"Nome de tema inválido: {nome!r}")
    return dict(temas)


# Nome do tema e rótulo. A ordem é a da lista de temas e a dos imports de
# ``app.css``.
TEMAS = validar_temas(
    {
        "oficial": "Oficial",
        "verde": "Verde",
        "terracota": "Terracota",
        "contraste": "Alto contraste",
    }
)

# Layouts concretos dos templates (docs/specs/v8/templates.md): nome e arquivo.
# É a única lista de onde sai o layout de uma zona.
LAYOUTS = {
    "landing": "v8/layouts/landing.html",
    "app_topbar": "v8/layouts/app_topbar.html",
    "app_sidebar": "v8/layouts/app_sidebar.html",
    "minimal": "v8/layouts/minimal.html",
}
LAYOUT_PADRAO = "app_sidebar"

_TAMANHO_AVATAR = (128, 128)


@dataclass(frozen=True)
class Zona:
    """Zona SPA: trecho de ``/v8/`` cujo miolo é do Vue Router.

    ``layout`` é um dos nomes de ``LAYOUTS``. Outro valor é erro na carga do
    projeto, porque as zonas são declaradas no módulo.
    """

    nome: str
    prefixo: str
    titulo: str
    menu_ativo: str | None = None
    exige: object = None
    layout: str = LAYOUT_PADRAO

    def __post_init__(self):
        if self.layout not in LAYOUTS:
            raise ValueError(f"Layout desconhecido na zona {self.nome}: {self.layout}")


# Cada zona é declarada uma única vez, aqui. As rotas Django e o JSON global
# saem deste registro.
ZONAS = {
    "demo-spa": Zona(
        "demo-spa", "demo/spa", "Demonstração SPA", "demo-spa", SUPERUSUARIO
    ),
}


def tema_em_vigor(cookies, tema=None):
    """Tema da página: o que ela fixa, senão o do cookie, senão o padrão.

    Só nomes do registro passam. ``tema`` é o da página de prévia de um tema.
    """
    if tema in TEMAS:
        return tema
    escolhido = (cookies or {}).get(COOKIE_TEMA)
    return escolhido if escolhido in TEMAS else TEMA_PADRAO


def preferencias(cookies, tema=None):
    """Lê tema, modo e sidebar dos cookies, aceitando só os valores previstos.

    Valor fora da lista é descartado: o tema volta ao padrão, o modo fica
    ``None`` (o CSS segue o sistema) e a sidebar volta ao padrão.
    """
    cookies = cookies or {}
    modo = cookies.get(COOKIE_MODO)
    sidebar = cookies.get(COOKIE_SIDEBAR)
    return {
        "tema": tema_em_vigor(cookies, tema),
        "modo": modo if modo in MODOS else None,
        "sidebar": sidebar if sidebar in SIDEBARS else SIDEBAR_PADRAO,
    }


def cookie_tema(nome):
    """Parâmetros de ``set_cookie`` para escolher o tema, ou ``None``.

    Só um nome do registro produz cookie. O navegador não precisa lê-lo: o
    Django emite o tema no HTML.
    """
    if nome not in TEMAS:
        return None
    return {
        "key": COOKIE_TEMA,
        "value": nome,
        "max_age": _IDADE_COOKIE,
        "path": URL_BASE,
        "samesite": "Lax",
        "httponly": True,
        "secure": not settings.DEBUG,
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
    modo = preferencias.get("modo")
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
        "tema": tema if tema in TEMAS else TEMA_PADRAO,
        "modo": modo if modo in MODOS else None,
        "sidebar": sidebar if sidebar in SIDEBARS else SIDEBAR_PADRAO,
    }
