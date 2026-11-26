"""Rotas do portal com o v8 ligado na raiz (docs/specs/v8/portal.md).

Escolhidas pelo ``PortalV8Middleware`` quando o cookie ``v8_portal`` é válido.
As rotas migradas para o v8 vêm primeiro; todo o resto é o ``cmj.urls``
inteiro, com os mesmos caminhos e nomes.
"""

from django.urls.conf import include, re_path

import cmj.urls
from cmj.urls import handler403  # noqa: F401  (o Django lê do urlconf da requisição)
from cmj.v8 import views

urlpatterns = [
    re_path(r"^$", views.InicioView.as_view(), name="portal_inicio"),
    re_path(r"", include(cmj.urls)),
]
