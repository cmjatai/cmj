from django.conf.urls import include, url

from cmj.ouvidoria.views import DenunciaAnonimaFormView, SolicitacaoDetailView,\
    SolicitacaoListView

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns_ouvidoria = [

    url(r'^fale-conosco/ouvidoria/denuncia-anonima/?$',
        DenunciaAnonimaFormView.as_view(), name='denuncia_form'),

    url(r'^fale-conosco/ouvidoria/solicitacao/(?P<pk>[0-9]+)/?$',
        SolicitacaoDetailView.as_view(), name='solicitacao_detail'),

    url(r'^fale-conosco/ouvidoria/solicitacao/?$',
        SolicitacaoListView.as_view(), name='solicitacao_list'),

]

urlpatterns = [
    url(r'', include(urlpatterns_ouvidoria)),


]
