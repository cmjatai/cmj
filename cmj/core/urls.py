from django.conf.urls import url, include
from django.contrib.auth import views

from cmj.core.forms import LoginForm
from cmj.core.views import CepCrud, RegiaoMunicipalCrud, DistritoCrud,\
    BairroCrud, TipoLogradouroCrud, LogradouroCrud, TrechoCrud, ImportCepView

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    url(r'^login/$',
        views.login, {'template_name': 'core/login.html',
                      'authentication_form': LoginForm,
                      'extra_context': {
                          'fluid': '-fluid'
                      }},
        name='login'),

    url(r'^logout/$', views.logout,
        {'next_page': '/login'}, name='logout', ),

    url(r'^sistema/core/cep/import',
        ImportCepView.as_view(), name="cep_import"),
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
