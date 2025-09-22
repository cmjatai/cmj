from django.urls.conf import re_path, include

from cmj.loa.dashboards import LoaDashboardView
from cmj.loa.views import LoaCrud, EmendaLoaCrud, OficioAjusteLoaCrud,\
    RegistroAjusteLoaCrud, AgrupamentoCrud, SubFuncaoCrud, UnidadeOrcamentariaCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    re_path(
        r'^loa',
        include(
            LoaCrud.get_urls() +
            EmendaLoaCrud.get_urls() +
            OficioAjusteLoaCrud.get_urls() +
            RegistroAjusteLoaCrud.get_urls() +
            AgrupamentoCrud.get_urls() +
            UnidadeOrcamentariaCrud.get_urls() +
            SubFuncaoCrud.get_urls()
        )
    ),

    re_path(r'^loa/dash', LoaDashboardView.as_view(),
        name='loa_dashboard'),

]
