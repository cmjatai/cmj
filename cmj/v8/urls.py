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

# Troca de portal (docs/specs/v8/portal.md): só POST, com CSRF.
urlpatterns_portal = [
    re_path(
        r"^v8/portal/ativar/$",
        views.PortalAtivarView.as_view(),
        name="portal_ativar",
    ),
    re_path(
        r"^v8/portal/desativar/$",
        views.PortalDesativarView.as_view(),
        name="portal_desativar",
    ),
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

# Uma rota por layout: o nome vem do registro, nunca do caminho pedido.
urlpatterns_demo_layouts = [
    re_path(
        rf"^v8/demo/layouts/{re.escape(nome)}/$",
        views.DemoLayoutView.as_view(layout=nome),
        name=f"demo_layout_{nome}",
    )
    for nome in s_global.LAYOUTS
]

# Design system. Prévia e escolha: uma rota por tema do registro, e o nome do
# tema vem dele, nunca do caminho pedido.
urlpatterns_ds = (
    [
        re_path(r"^v8/ds/$", views.DsVitrineView.as_view(), name="ds"),
        re_path(r"^v8/ds/temas/$", views.DsTemasView.as_view(), name="ds_temas"),
    ]
    + [
        re_path(
            rf"^v8/ds/temas/{re.escape(nome)}/$",
            views.DsVitrineView.as_view(tema=nome),
            name=f"ds_tema_{nome}",
        )
        for nome in s_global.TEMAS
    ]
    + [
        re_path(
            rf"^v8/ds/temas/{re.escape(nome)}/usar/$",
            views.DsTemaUsarView.as_view(tema=nome),
            name=f"ds_tema_usar_{nome}",
        )
        for nome in s_global.TEMAS
    ]
)

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
    + urlpatterns_portal
    + urlpatterns_demo
    + urlpatterns_demo_layouts
    + urlpatterns_ds
    + urlpatterns_zonas
    + [
        re_path(
            r"^v8/(?P<resto>.*)$",
            views.NaoEncontradoV8View.as_view(),
            name="nao_encontrado",
        ),
    ]
)
