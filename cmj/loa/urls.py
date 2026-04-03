from django.urls.conf import include, re_path

from cmj.loa import views
from cmj.loa.dashboards import LoaDashboardView

from .apps import AppConfig

app_name = AppConfig.name


urlpatterns = [
    re_path(
        r"^loa",
        include(
            views.v_loa.LoaCrud.get_urls()
            + views.v_agrupamento.AgrupamentoCrud.get_urls()
            + views.v_ajusteloa.OficioAjusteLoaCrud.get_urls()
            + views.v_ajusteloa.RegistroAjusteLoaCrud.get_urls()
            + views.v_emendaloa.EmendaLoaCrud.get_urls()
            + views.v_financeiro_execucao.EmpenhoCrud.get_urls()
            + views.v_financeiro_orcamento.DespesaCrud.get_urls()
            + views.v_financeiro_orcamento.UnidadeOrcamentariaCrud.get_urls()
            + views.v_financeiro_orcamento.SubFuncaoCrud.get_urls()
            + views.v_prestacaoconta.PrestacaoContaLoaCrud.get_urls()
            + views.v_prestacaoconta.PrestacaoContaRegistroCrud.get_urls()
        ),
    ),
    re_path(r"^loa/dash", LoaDashboardView.as_view(), name="loa_dashboard"),
    re_path(r"^sistema/entidade", include(views.v_entidade.EntidadeCrud.get_urls())),
]
