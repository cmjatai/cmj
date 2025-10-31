from django.urls.conf import re_path, include

from cmj.loa.dashboards import LoaDashboardView
from cmj.loa import views

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    re_path(
        r'^loa',
        include(
            views.LoaCrud.get_urls() +
            views.EmendaLoaCrud.get_urls() +
            views.OficioAjusteLoaCrud.get_urls() +
            views.RegistroAjusteLoaCrud.get_urls() +
            views.AgrupamentoCrud.get_urls() +
            views.UnidadeOrcamentariaCrud.get_urls() +
            views.SubFuncaoCrud.get_urls() +
            views.PrestacaoContaLoaCrud.get_urls() +
            views.PrestacaoContaRegistroCrud.get_urls()
        )
    ),

    re_path(r'^loa/dash', LoaDashboardView.as_view(),
        name='loa_dashboard'),

    re_path(r'^sistema/entidade',
        include(views.EntidadeCrud.get_urls())),
]
