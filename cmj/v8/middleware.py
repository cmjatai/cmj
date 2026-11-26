"""Middleware do v8 (docs/specs/v8/portal.md).

Só lê o cookie e escolhe o conjunto de rotas da requisição. A regra fica em
``cmj/v8/services/s_portal.py``.
"""

from cmj.v8.services import s_portal


class PortalV8Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if s_portal.ativo(request.COOKIES.get(s_portal.COOKIE_PORTAL)):
            request.urlconf = s_portal.URLCONF_RAIZ
            request.v8_portal = True
        return self.get_response(request)
