"""Rotas do v8. Todas casam só com caminhos iniciados por ``/v8/``.

A ordem importa: páginas, fragmentos e endpoints, depois uma rota por zona SPA
e, por último, o 404 do v8.
"""

import re

from django.urls.conf import re_path

from cmj.v8 import views
from cmj.v8.services import s_global

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_paginas = [
    re_path(r"^v8/$", views.InicioView.as_view(), name="inicio"),
]

urlpatterns_demo = [
    re_path(
        r"^v8/demo/clientes/$",
        views.DemoClientesView.as_view(),
        name="demo_clientes",
    ),
    re_path(
        r"^v8/demo/clientes/arquivar/$",
        views.DemoArquivarView.as_view(),
        name="demo_clientes_arquivar",
    ),
    re_path(
        r"^v8/demo/clientes/(?P<pk>\d+)/$",
        views.DemoClienteView.as_view(),
        name="demo_cliente",
    ),
    re_path(
        r"^v8/_frag/demo/cliente/(?P<pk>\d+)/historico/$",
        views.DemoClienteHistoricoFragmento.as_view(),
        name="demo_frag_cliente_historico",
    ),
    re_path(
        r"^v8/demo/api/clientes/$",
        views.DemoApiClientesView.as_view(),
        name="demo_api_clientes",
    ),
    re_path(
        r"^v8/demo/api/clientes/(?P<pk>\d+)/$",
        views.DemoApiClienteView.as_view(),
        name="demo_api_cliente",
    ),
    re_path(
        r"^v8/demo/api/negado/$",
        views.DemoApiNegadoView.as_view(),
        name="demo_api_negado",
    ),
]

# Uma rota por zona: o prefixo e qualquer subcaminho, com ou sem barra final.
urlpatterns_zonas = [
    re_path(
        rf"^v8/{re.escape(zona.prefixo)}(?:/(?P<subcaminho>.*))?$",
        views.ZonaV8View.as_view(zona=zona.nome),
        name=f"zona_{zona.nome}",
    )
    for zona in s_global.ZONAS.values()
]

urlpatterns = (
    urlpatterns_paginas
    + urlpatterns_demo
    + urlpatterns_zonas
    + [
        re_path(
            r"^v8/(?P<resto>.*)$",
            views.NaoEncontradoV8View.as_view(),
            name="nao_encontrado",
        ),
    ]
)
