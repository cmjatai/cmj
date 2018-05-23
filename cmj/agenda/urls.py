from django.conf.urls import include, url

from cmj.agenda.views import EventoCrud, TipoEventoCrud

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns_agenda = [

    # url(r'^fale-conosco/ouvidoria',
    # OuvidoriaPaginaInicialView.as_view(), name='ouvidoria_pagina_inicial'),
    url(r'^evento/', include(EventoCrud.get_urls())),
    url(r'^sistema/agenda/tipoevento/',
        include(TipoEventoCrud.get_urls())),
]

urlpatterns = [
    url(r'', include(urlpatterns_agenda)),
]
