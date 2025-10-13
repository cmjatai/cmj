from django.conf import settings
from django.contrib.auth import views as v_auth
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.views import PasswordResetDoneView,\
    PasswordResetConfirmView, PasswordResetCompleteView, LogoutView
from django.urls.conf import re_path, include
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView

from cmj.core.forms_auth import NovaSenhaForm
from cmj.core.views import CepCrud, RegiaoMunicipalCrud, DistritoCrud,\
    BairroCrud, TipoLogradouroCrud, LogradouroCrud, TrechoCrud, \
    TrechoJsonSearchView, TrechoJsonView, AreaTrabalhoCrud,\
    OperadorAreaTrabalhoCrud, PartidoCrud, ImpressoEnderecamentoCrud,\
    NotificacaoRedirectView, chanel_index, chanel_room, time_refresh_log_test,\
    app_vue_view_v2018, app_vue_view_v2025, template_render, CertidaoPublicacaoCrud, BiView, \
    MediaPublicView, PesquisarAuditLogView
from cmj.core.views_auth import CmjUserChangeView, CmjLoginView,\
    UserCrud, CmjPasswordResetView, CmjPasswordResetEncaminhadoView,\
    CmjPasswordResetConfirmView, CmjPasswordResetCompleteView

from .apps import AppConfig


app_name = AppConfig.name

user_urlpatterns = [
    # password_reset
    re_path(r'^user/recuperar-senha/email/$',
            CmjPasswordResetView.as_view(),
            name='recuperar_senha_email'),

    # password_reset_done
    re_path(r'^user/recuperar-senha/finalizado/$',
            CmjPasswordResetEncaminhadoView.as_view(),
            name='recuperar_senha_finalizado'),

    # password_reset_confirme
    re_path(r'^user/recuperar-senha/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
            CmjPasswordResetConfirmView.as_view(),
            name='recuperar_senha_confirma'),

    # password_reset_complete
    re_path(r'^user/recuperar-senha/completo/$',
            CmjPasswordResetCompleteView.as_view(),
            name='password_reset_complete'),

    re_path(r'^user/edit/$', login_required(CmjUserChangeView.as_view()),
            name='cmj_user_change'),

    re_path(r'^login/$', CmjLoginView.as_view(), name='login'),
    re_path(r'^logout/$', LogoutView.as_view(),
            {'next_page': '/'}, name='logout', ),

    re_path(r'^template/(?P<template_name>[^/]+)$',
            template_render, name='template_render'),

    re_path(r'^sistema/auditlog/$', PesquisarAuditLogView.as_view(),
            name='pesquisar_auditlog'),
]

if settings.DEBUG:
    user_urlpatterns += [
        re_path(r'^channel$', chanel_index, name='channel_index'),

        re_path(r'^channel/(?P<room_name>[^/]+)/$',
                chanel_room, name='channel_room'),

        re_path(r'^time-refresh/$',
                time_refresh_log_test, name='time_refresh_log_test_index'),
    ]


urlpatterns = user_urlpatterns + [

    re_path(r'^media/(?P<path>.*)$',
            MediaPublicView.as_view(), name='mediapublic_view'),

    # url(r'^enderecos/', login_required(
    #    TrechoSearchView.as_view()), name='search_view'),

    re_path(r'^areatrabalho', include(AreaTrabalhoCrud.get_urls() +
                                      OperadorAreaTrabalhoCrud.get_urls())),

    re_path(r'^cert', include(CertidaoPublicacaoCrud.get_urls())),

    re_path(r'^notificacao/(?P<pk>[0-9]+)$', NotificacaoRedirectView.as_view(),
            name='notificacao_redirect'),


    re_path(r'^estatisticas$', BiView.as_view(),
            name='bi_render'),

    re_path(r'^api/enderecos.json', TrechoJsonSearchView.as_view(
        {'get': 'list'}), name='trecho_search_rest_json'),
    re_path(r'^api/trecho.json/(?P<pk>[0-9]+)$', TrechoJsonView.as_view(
        {'get': 'retrieve'}), name='trecho_rest_json'),

    re_path(r'^sistema/core/cep', include(CepCrud.get_urls())),
    re_path(r'^sistema/core/regiaomunicipal',
            include(RegiaoMunicipalCrud.get_urls())),
    re_path(r'^sistema/core/distrito', include(DistritoCrud.get_urls())),
    re_path(r'^sistema/core/bairro', include(BairroCrud.get_urls())),
    re_path(r'^sistema/core/tipologradouro',
            include(TipoLogradouroCrud.get_urls())),
    re_path(r'^sistema/core/logradouro', include(LogradouroCrud.get_urls())),


    re_path(r'^online/',
            app_vue_view_v2018, name='app_vue_view_v2018_url'),

    re_path(r'^2025/',
            app_vue_view_v2025, name='app_vue_view_v2025_url'),


    re_path(r'^sistema/core/trecho', include(TrechoCrud.get_urls())),

    re_path(r'^sistema/usuario', include(UserCrud.get_urls())),

    re_path(r'^sistema/core/impressoenderecamento',
            include(ImpressoEnderecamentoCrud.get_urls())),

    #url(r'^sistema/parlamentar/partido/', include(PartidoCrud.get_urls())),

    re_path(r'^sistema/$', permission_required(
        'core.menu_tabelas_auxiliares', login_url='cmj.core:login')(
        TemplateView.as_view(template_name='cmj_sistema.html')),
        name="tabelas_auxiliares"),

    re_path(r'^sistema$', permission_required(
        'core.menu_tabelas_auxiliares', login_url='cmj.core:login')(
        TemplateView.as_view(template_name='cmj_sistema.html')),
        name="tabelas_auxiliares"),

]
