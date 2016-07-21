from django.conf.urls import url, include
from django.contrib.auth import views as v_auth
from django.contrib.auth.decorators import permission_required, login_required
from django.views.generic.base import TemplateView

from cmj.core.forms import LoginForm
from cmj.core.views import CepCrud, RegiaoMunicipalCrud, DistritoCrud,\
    BairroCrud, TipoLogradouroCrud, LogradouroCrud, TrechoCrud, \
    TrechoJsonSearchView, TrechoJsonView, AreaTrabalhoCrud,\
    OperadorAreaTrabalhoCrud, PartidoCrud, ImpressoEnderecamentoCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    url(r'^login/$', v_auth.login, {'template_name': 'core/login.html',
                                    'authentication_form': LoginForm,
                                    'extra_context': {
                                        'fluid': '-fluid'
                                    }}, name='login'),
    url(r'^logout/$', v_auth.logout, {'next_page': '/login'}, name='logout', ),

    # url(r'^enderecos/', login_required(
    #    TrechoSearchView.as_view()), name='search_view'),

    url(r'^areatrabalho/', include(AreaTrabalhoCrud.get_urls() +
                                   OperadorAreaTrabalhoCrud.get_urls())),

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
