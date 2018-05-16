from django.conf.urls import include, url

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns_agenda = [

    # url(r'^fale-conosco/ouvidoria',
    # OuvidoriaPaginaInicialView.as_view(), name='ouvidoria_pagina_inicial'),

]

urlpatterns = [
    url(r'', include(urlpatterns_agenda)),
]
