from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib.auth import views as v_auth
from django.views.generic.base import TemplateView
from django.views.static import serve as view_static_server

from cmj import settings
from cmj.core import views
from cmj.core.forms import LoginForm
from cmj.core.views import CepCrud, RegiaoMunicipalCrud, DistritoCrud,\
    BairroCrud, TipoLogradouroCrud, LogradouroCrud, TrechoCrud, \
    EnderecoPesquisaView, LogradouroSearchView

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    url(r'^login/$', v_auth.login, {'template_name': 'core/login.html',
                                    'authentication_form': LoginForm,
                                    'extra_context': {
                                        'fluid': '-fluid'
                                    }}, name='login'),
    url(r'^logout/$', v_auth.logout, {'next_page': '/login'}, name='logout', ),

    url(r'^enderecos/', LogradouroSearchView.as_view(), name='search_view'),

    url(r'^sistema/$', TemplateView.as_view(template_name='cmj_sistema.html')),

    url(r'^sistema/core/cep/', include(CepCrud.get_urls())),
    url(r'^sistema/core/regiaomunicipal/',
        include(RegiaoMunicipalCrud.get_urls())),
    url(r'^sistema/core/distrito/', include(DistritoCrud.get_urls())),
    url(r'^sistema/core/bairro/', include(BairroCrud.get_urls())),
    url(r'^sistema/core/tipologradouro/',
        include(TipoLogradouroCrud.get_urls())),
    url(r'^sistema/core/logradouro/', include(LogradouroCrud.get_urls())),
    url(r'^sistema/core/trecho/', include(TrechoCrud.get_urls())),
]
