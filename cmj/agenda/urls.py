from django.urls.conf import include, re_path

from cmj.agenda.views import EventoCrud, TipoEventoCrud

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns_agenda = [
    # url(r'^fale-conosco/ouvidoria',
    # OuvidoriaPaginaInicialView.as_view(), name='ouvidoria_pagina_inicial'),
    re_path(r"^evento", include(EventoCrud.get_urls())),
    re_path(r"^sistema/agenda/tipoevento", include(TipoEventoCrud.get_urls())),
]

urlpatterns = [
    re_path(r"", include(urlpatterns_agenda)),
]
