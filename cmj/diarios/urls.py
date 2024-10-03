from django.urls.conf import re_path, include

from cmj.diarios.views import TipoDeDiarioCrud, DiarioOficialCrud,\
    VinculoDocDiarioOficialCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    re_path(r'^diariooficial',
        include(
            DiarioOficialCrud.get_urls() +
            VinculoDocDiarioOficialCrud.get_urls()
        )),
    re_path(r'^sistema/diarios/tipodediario',
        include(TipoDeDiarioCrud.get_urls())),
]
