
from sapl.relatorios.view_reports.mixins import RelatorioMixin
from django.views.generic import TemplateView


class View(RelatorioMixin, TemplateView):
    pass