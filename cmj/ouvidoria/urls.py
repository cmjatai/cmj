from django.urls.conf import include, re_path

from cmj.ouvidoria.views import (
    DenunciaAnonimaFormView,
    OuvidoriaPaginaInicialView,
    SolicitacaoDetailView,
    SolicitacaoFormView,
    SolicitacaoInteractionView,
    SolicitacaoListView,
    SolicitacaoManageListView,
    SolicitacaoMensagemAnexoView,
    SolicitacaoMensagemRedirect,
)

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_ouvidoria = [
    re_path(
        r"^fale-conosco/ouvidoria_disabled/denuncia-anonima/?$",
        DenunciaAnonimaFormView.as_view(),
        name="denuncia_form",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled/solicitacao/(?P<pk>[0-9]+)/?$",
        SolicitacaoDetailView.as_view(),
        name="solicitacao_detail",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled/solicitacao/minhas/?$",
        SolicitacaoListView.as_view(),
        name="solicitacao_list",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled/solicitacao/manage/?$",
        SolicitacaoManageListView.as_view(),
        name="solicitacao_manage_list",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled/solicitacao/registrar/?$",
        SolicitacaoFormView.as_view(),
        name="solicitacao_create",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled/solicitacao/(?P<pk>[0-9]+)/interact$",
        SolicitacaoInteractionView.as_view(),
        name="solicitacao_interact",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled/solicitacao/P(?P<hash>[0-9A-Fa-f]+)/(?P<pk>\d+)$",
        SolicitacaoInteractionView.as_view(),
        name="solicitacao_interact_hash",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled/solicitacao/(?P<pk>[0-9]+)/mensagem",
        SolicitacaoMensagemRedirect.as_view(),
        name="mensagemsolicitacao_detail",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled/mensagem/(?P<pk>[0-9]+)/anexo",
        SolicitacaoMensagemAnexoView.as_view(),
        name="anexo_mensagem_view",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled/mensagem/P(?P<hash>[0-9A-Fa-f]+)/(?P<pk>\d+)/anexo",
        SolicitacaoMensagemAnexoView.as_view(),
        name="anexo_mensagem_view_hash",
    ),
    re_path(
        r"^fale-conosco/ouvidoria_disabled",
        OuvidoriaPaginaInicialView.as_view(),
        name="ouvidoria_pagina_inicial",
    ),
]

urlpatterns = [
    re_path(r"", include(urlpatterns_ouvidoria)),
]
