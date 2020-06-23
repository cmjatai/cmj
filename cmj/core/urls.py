from django.conf.urls import url, include
from django.contrib.auth import views as v_auth
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.views import PasswordResetDoneView,\
    PasswordResetConfirmView, PasswordResetCompleteView, LogoutView
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from cmj.core.forms_auth import NovaSenhaForm
from cmj.core.views import CepCrud, RegiaoMunicipalCrud, DistritoCrud,\
    BairroCrud, TipoLogradouroCrud, LogradouroCrud, TrechoCrud, \
    TrechoJsonSearchView, TrechoJsonView, AreaTrabalhoCrud,\
    OperadorAreaTrabalhoCrud, PartidoCrud, ImpressoEnderecamentoCrud,\
    NotificacaoRedirectView, chanel_index, chanel_room, time_refresh_log_test,\
    app_vue_view, template_render, CertidaoPublicacaoCrud, BiView
from cmj.core.views_auth import CmjUserChangeView, CmjLoginView,\
    CmjPasswordResetView, UserCrud, CmjPasswordResetConfirmView,\
    CmjPasswordResetEncaminhadoView
from cmj.core.views_search import CmjSearchView

from .apps import AppConfig


app_name = AppConfig.name

user_urlpatterns = [

    url(r'^user/edit/$', login_required(CmjUserChangeView.as_view()),
        name='cmj_user_change'),

    url(r'^user/recuperar-senha/email/$',
        CmjPasswordResetView.as_view(),
        name='recuperar_senha_email'),

    url(r'^user/recuperar-senha/finalizado/$',
        CmjPasswordResetEncaminhadoView.as_view(),
        name='recuperar_senha_finalizado'),

    url(r'^user/recuperar-senha/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        CmjPasswordResetConfirmView.as_view(),
        name='recuperar_senha_confirma'),

    url(r'^user/recuperar-senha/completo/$',
        PasswordResetCompleteView.as_view(),
        {'template_name': 'core/user/recuperar_senha_completo.html'},
        name='recuperar_senha_completo'),

    url(r'^login/$', CmjLoginView.as_view(), name='login'),

    url(r'^logout/$', LogoutView.as_view(),
        {'next_page': '/'}, name='logout', ),


    url(r'^channel$', chanel_index, name='channel_index'),
    url(r'^channel/(?P<room_name>[^/]+)/$',
        chanel_room, name='channel_room'),
    url(r'^time-refresh/$',
        time_refresh_log_test, name='time_refresh_log_test_index'),

    url(r'^online/',
        app_vue_view, name='app_vue_view_url'),

    url(r'^template/(?P<template_name>[^/]+)$',
        template_render, name='template_render'),



    url(r'^sistema/search/', CmjSearchView(), name='haystack_search'),

]


urlpatterns = user_urlpatterns + [


    # url(r'^enderecos/', login_required(
    #    TrechoSearchView.as_view()), name='search_view'),

    url(r'^areatrabalho/', include(AreaTrabalhoCrud.get_urls() +
                                   OperadorAreaTrabalhoCrud.get_urls())),

    url(r'^cert/', include(CertidaoPublicacaoCrud.get_urls())),

    url(r'^notificacao/(?P<pk>[0-9]+)$', NotificacaoRedirectView.as_view(),
        name='notificacao_redirect'),


    url(r'^estatisticas/$', BiView.as_view(),
        name='bi_render'),


    url(r'^api/enderecos.json', TrechoJsonSearchView.as_view(
        {'get': 'list'}), name='trecho_search_rest_json'),
    url(r'^api/trecho.json/(?P<pk>[0-9]+)$', TrechoJsonView.as_view(
        {'get': 'retrieve'}), name='trecho_rest_json'),

    url(r'^sistema/core/cep/', include(CepCrud.get_urls())),
    url(r'^sistema/core/regiaomunicipal/',
        include(RegiaoMunicipalCrud.get_urls())),
    url(r'^sistema/core/distrito/', include(DistritoCrud.get_urls())),
    url(r'^sistema/core/bairro/', include(BairroCrud.get_urls())),
    url(r'^sistema/core/tipologradouro/',
        include(TipoLogradouroCrud.get_urls())),
    url(r'^sistema/core/logradouro/', include(LogradouroCrud.get_urls())),



    url(r'^sistema/core/trecho/', include(TrechoCrud.get_urls())),

    url(r'^sistema/usuario/', include(UserCrud.get_urls())),

    url(r'^sistema/core/impressoenderecamento/',
        include(ImpressoEnderecamentoCrud.get_urls())),

    #url(r'^sistema/parlamentar/partido/', include(PartidoCrud.get_urls())),

    url(r'^sistema/$', permission_required(
        'core.menu_tabelas_auxiliares', login_url='cmj.core:login')(
        TemplateView.as_view(template_name='cmj_sistema.html')),
        name="tabelas_auxiliares"),

    url(r'^sistema$', permission_required(
        'core.menu_tabelas_auxiliares', login_url='cmj.core:login')(
        TemplateView.as_view(template_name='cmj_sistema.html')),
        name="tabelas_auxiliares"),
]
