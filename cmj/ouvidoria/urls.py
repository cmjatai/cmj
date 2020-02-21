from django.conf.urls import include, url

from cmj.ouvidoria.views import DenunciaAnonimaFormView, \
    SolicitacaoDetailView, SolicitacaoManageListView, SolicitacaoListView, \
    SolicitacaoFormView, SolicitacaoInteractionView,\
    SolicitacaoMensagemRedirect, OuvidoriaPaginaInicialView,\
    SolicitacaoMensagemAnexoView

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns_ouvidoria = [

    url(r'^fale-conosco/ouvidoria/denuncia-anonima/?$',
        DenunciaAnonimaFormView.as_view(), name='denuncia_form'),

    url(r'^fale-conosco/ouvidoria/solicitacao/(?P<pk>[0-9]+)/?$',
        SolicitacaoDetailView.as_view(), name='solicitacao_detail'),

    url(r'^fale-conosco/ouvidoria/solicitacao/minhas/?$',
        SolicitacaoListView.as_view(), name='solicitacao_list'),

    url(r'^fale-conosco/ouvidoria/solicitacao/manage/?$',
        SolicitacaoManageListView.as_view(), name='solicitacao_manage_list'),


    url(r'^fale-conosco/ouvidoria/solicitacao/registrar/?$',
        SolicitacaoFormView.as_view(), name='solicitacao_create'),

    url(r'^fale-conosco/ouvidoria/solicitacao/(?P<pk>[0-9]+)/interact$',
        SolicitacaoInteractionView.as_view(), name='solicitacao_interact'),

    url(r'^fale-conosco/ouvidoria/solicitacao/P(?P<hash>[0-9A-Fa-f]+)/(?P<pk>\d+)$',
        SolicitacaoInteractionView.as_view(), name='solicitacao_interact_hash'),


    url(r'^fale-conosco/ouvidoria/solicitacao/(?P<pk>[0-9]+)/mensagem',
        SolicitacaoMensagemRedirect.as_view(), name='mensagemsolicitacao_detail'),

    url(r'^fale-conosco/ouvidoria/mensagem/(?P<pk>[0-9]+)/anexo',
        SolicitacaoMensagemAnexoView.as_view(), name='anexo_mensagem_view'),

    url(r'^fale-conosco/ouvidoria/mensagem/P(?P<hash>[0-9A-Fa-f]+)/(?P<pk>\d+)/anexo',
        SolicitacaoMensagemAnexoView.as_view(), name='anexo_mensagem_view_hash'),

    url(r'^fale-conosco/ouvidoria',
        OuvidoriaPaginaInicialView.as_view(), name='ouvidoria_pagina_inicial'),


]

urlpatterns = [
    url(r'', include(urlpatterns_ouvidoria)),


]
