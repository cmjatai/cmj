from django.conf.urls import url, include

from cmj.diarios.views import TipoDeDiarioCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    url(r'^sistema/diarios/tipodediario/',
        include(TipoDeDiarioCrud.get_urls())),
]
