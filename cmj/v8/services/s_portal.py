"""Troca de portal: o v8 nas mesmas rotas do portal, por cookie assinado.

Regras em docs/specs/v8/portal.md. Sem o cookie, nada muda: o Django resolve
com ``cmj.urls``. Com ele, resolve com ``URLCONF_RAIZ``, que atende ``/`` com a
página inicial do v8 e entrega todo o resto ao ``cmj.urls``.

As funções recebem o usuário e valores simples. Nenhuma recebe a requisição.
"""

from django.conf import settings
from django.core import signing
from django.utils.http import url_has_allowed_host_and_scheme

COOKIE_PORTAL = "v8_portal"
SALT = "cmj.v8.portal"
# Validade do cookie, em segundos: conferida na leitura e repetida no max_age.
VALIDADE = 12 * 60 * 60
URLCONF_RAIZ = "cmj.v8.urls_raiz"
DESTINO_PADRAO = "/"


def _assinador():
    return signing.TimestampSigner(salt=SALT)


def pode_ativar(usuario):
    """Só superusuário liga o v8 na raiz do portal."""
    return bool(
        usuario is not None and usuario.is_authenticated and usuario.is_superuser
    )


def cookie_ativar(usuario):
    """Parâmetros de ``set_cookie`` para ligar o v8, ou ``None``.

    O valor é o pk de quem ligou, assinado com data. Continua valendo depois do
    logout, até expirar.
    """
    if not pode_ativar(usuario):
        return None
    return {
        "key": COOKIE_PORTAL,
        "value": _assinador().sign(str(usuario.pk)),
        "max_age": VALIDADE,
        "path": "/",
        "samesite": "Lax",
        "httponly": True,
        "secure": not settings.DEBUG,
    }


def cookie_desativar():
    """Parâmetros de ``delete_cookie`` para desligar o v8."""
    return {"key": COOKIE_PORTAL, "path": "/", "samesite": "Lax"}


def ativo(valor_cookie):
    """Diz se o valor do cookie liga o v8: assinatura correta e dentro da validade."""
    if not valor_cookie:
        return False
    try:
        _assinador().unsign(valor_cookie, max_age=VALIDADE)
    except signing.BadSignature:
        return False
    return True


def destino(proximo, host):
    """Caminho para onde voltar: ``proximo`` se for caminho do mesmo host, senão ``/``."""
    if (
        isinstance(proximo, str)
        and proximo.startswith("/")
        and not proximo.startswith("//")
        and "\\" not in proximo
        and url_has_allowed_host_and_scheme(proximo, allowed_hosts={host})
    ):
        return proximo
    return DESTINO_PADRAO
