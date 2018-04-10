from django.conf.urls import url, include
from django.contrib.auth import views as v_auth
from django.contrib.auth.decorators import permission_required, login_required
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

from cmj.core.forms_auth import RecuperarSenhaForm, NovaSenhaForm, LoginForm
from cmj.core.views import CepCrud, RegiaoMunicipalCrud, DistritoCrud,\
    BairroCrud, TipoLogradouroCrud, LogradouroCrud, TrechoCrud, \
    TrechoJsonSearchView, TrechoJsonView, AreaTrabalhoCrud,\
    OperadorAreaTrabalhoCrud, PartidoCrud, ImpressoEnderecamentoCrud,\
    NotificacaoRedirectView
from cmj.core.views_auth import CmjUserChangeView, CmjLoginView,\
    CmjPasswordResetView
from cmj.settings import EMAIL_SEND_USER

from .apps import AppConfig


app_name = AppConfig.name

user_urlpatterns = [
    url(r'^user/edit/$', login_required(CmjUserChangeView.as_view()),
        name='cmj_user_change'),

    url(r'^user/recuperar-senha/email/$',
        CmjPasswordResetView.as_view(),
        name='recuperar_senha_email'),

    url(r'^user/recuperar-senha/finalizado/$',
        v_auth.password_reset_done,
        {'template_name': 'core/user/recupera_senha_email_enviado.html'},
        name='recuperar_senha_finalizado'),

    url(r'^user/recuperar-senha/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        v_auth.password_reset_confirm,
        {'post_reset_redirect': 'cmj.core:recuperar_senha_completo',
         'template_name': 'core/user/nova_senha_form.html',
         'set_password_form': NovaSenhaForm},
        name='recuperar_senha_confirma'),

    url(r'^user/recuperar-senha/completo/$',
        v_auth.password_reset_complete,
        {'template_name': 'core/user/recuperar_senha_completo.html'},
        name='recuperar_senha_completo'),

    url(r'^login/$', CmjLoginView.as_view(), name='login'),

    url(r'^logout/$', v_auth.logout,
        {'next_page': '/'}, name='logout', ),

]


urlpatterns = user_urlpatterns + [

    # url(r'^enderecos/', login_required(
    #    TrechoSearchView.as_view()), name='search_view'),

    url(r'^areatrabalho/', include(AreaTrabalhoCrud.get_urls() +
                                   OperadorAreaTrabalhoCrud.get_urls())),

    url(r'^notificacao/(?P<pk>[0-9]+)$', NotificacaoRedirectView.as_view(),
        name='notificacao_redirect'),


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

    url(r'^sistema/core/impressoenderecamento/',
        include(ImpressoEnderecamentoCrud.get_urls())),

    url(r'^sistema/parlamentar/partido/', include(PartidoCrud.get_urls())),

    url(r'^sistema/$', permission_required(
        'core.menu_tabelas_auxiliares', login_url='cmj.core:login')(
        TemplateView.as_view(template_name='cmj_sistema.html')),
        name="tabelas_auxiliares"),

    url(r'^sistema$', permission_required(
        'core.menu_tabelas_auxiliares', login_url='cmj.core:login')(
        TemplateView.as_view(template_name='cmj_sistema.html')),
        name="tabelas_auxiliares"),
]
