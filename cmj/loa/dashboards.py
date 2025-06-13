

from cmj.dashboard.dashboard import GridDashboard
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _


class LoaDashboardView(GridDashboard, TemplateView):
    """
    Dashboard para Leis Orçamentárias Anuais (LOA).
    """
    app_config = 'loa'
    container_css_class = 'container-fluid'


    def get_template_names(self):
        return ['dashboard/loa/loa_dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Dashboard de Leis Orçamentárias Anuais (LOA)')
        return context
