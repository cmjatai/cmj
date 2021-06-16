from django.conf.urls import url, include

from cmj.diarios.views import TipoDeDiarioCrud, DiarioOficialCrud,\
    VinculoDocDiarioOficialCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    url(r'^diariooficial',
        include(
            DiarioOficialCrud.get_urls() +
            VinculoDocDiarioOficialCrud.get_urls()
        )),
    url(r'^sistema/diarios/tipodediario',
        include(TipoDeDiarioCrud.get_urls())),
]
