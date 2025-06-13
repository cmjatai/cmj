

from cmj.dashboard.dashboard import GridDashboard


class LoaDashboardView(GridDashboard):
    """
    Dashboard para Leis Orçamentárias Anuais (LOA).
    """

    def get_template_names(self):
        return ['dashboard/loa/loa_dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Dashboard de Leis Orçamentárias Anuais (LOA)')
        return context
