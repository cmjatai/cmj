from django.urls.conf import re_path, include

from cmj.loa.views import LoaCrud, EmendaLoaCrud, OficioAjusteLoaCrud,\
    RegistroAjusteLoaCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    re_path(r'^loa',
        include(
            LoaCrud.get_urls() +
            EmendaLoaCrud.get_urls() +
            OficioAjusteLoaCrud.get_urls() +
            RegistroAjusteLoaCrud.get_urls()
        )
        ),
]
