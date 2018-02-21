from django.conf.urls import include, url

from cmj.ouvidoria.views import DenunciaAnonimaFormView, \
    SolicitacaoDetailView, SolicitacaoManageListView, SolicitacaoListView, \
    SolicitacaoFormView, SolicitacaoInteractionView

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


]

urlpatterns = [
    url(r'', include(urlpatterns_ouvidoria)),


]
