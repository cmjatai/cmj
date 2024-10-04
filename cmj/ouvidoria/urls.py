from django.urls.conf import re_path, include

from cmj.ouvidoria.views import DenunciaAnonimaFormView, \
    SolicitacaoDetailView, SolicitacaoManageListView, SolicitacaoListView, \
    SolicitacaoFormView, SolicitacaoInteractionView,\
    SolicitacaoMensagemRedirect, OuvidoriaPaginaInicialView,\
    SolicitacaoMensagemAnexoView

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns_ouvidoria = [

    re_path(r'^fale-conosco/ouvidoria/denuncia-anonima/?$',
        DenunciaAnonimaFormView.as_view(), name='denuncia_form'),

    re_path(r'^fale-conosco/ouvidoria/solicitacao/(?P<pk>[0-9]+)/?$',
        SolicitacaoDetailView.as_view(), name='solicitacao_detail'),

    re_path(r'^fale-conosco/ouvidoria/solicitacao/minhas/?$',
        SolicitacaoListView.as_view(), name='solicitacao_list'),

    re_path(r'^fale-conosco/ouvidoria/solicitacao/manage/?$',
        SolicitacaoManageListView.as_view(), name='solicitacao_manage_list'),


    re_path(r'^fale-conosco/ouvidoria/solicitacao/registrar/?$',
        SolicitacaoFormView.as_view(), name='solicitacao_create'),

    re_path(r'^fale-conosco/ouvidoria/solicitacao/(?P<pk>[0-9]+)/interact$',
        SolicitacaoInteractionView.as_view(), name='solicitacao_interact'),

    re_path(r'^fale-conosco/ouvidoria/solicitacao/P(?P<hash>[0-9A-Fa-f]+)/(?P<pk>\d+)$',
        SolicitacaoInteractionView.as_view(), name='solicitacao_interact_hash'),


    re_path(r'^fale-conosco/ouvidoria/solicitacao/(?P<pk>[0-9]+)/mensagem',
        SolicitacaoMensagemRedirect.as_view(), name='mensagemsolicitacao_detail'),

    re_path(r'^fale-conosco/ouvidoria/mensagem/(?P<pk>[0-9]+)/anexo',
        SolicitacaoMensagemAnexoView.as_view(), name='anexo_mensagem_view'),

    re_path(r'^fale-conosco/ouvidoria/mensagem/P(?P<hash>[0-9A-Fa-f]+)/(?P<pk>\d+)/anexo',
        SolicitacaoMensagemAnexoView.as_view(), name='anexo_mensagem_view_hash'),

    re_path(r'^fale-conosco/ouvidoria',
        OuvidoriaPaginaInicialView.as_view(), name='ouvidoria_pagina_inicial'),


]

urlpatterns = [
    re_path(r'', include(urlpatterns_ouvidoria)),


]
