

from logging import Filter

from django import forms
from cmj.dashboard.dashboard import Dashcard, GridDashboard
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from cmj.loa.models import Despesa, Loa
from django.db.models import Sum
from django_filters import FilterSet, CharFilter, ChoiceFilter, ModelChoiceFilter, ModelMultipleChoiceFilter, MultipleChoiceFilter

def choice_anos_loa():
    return [(ano, str(ano)) for ano in Despesa.objects.values_list('loa__ano', flat=True)]

class DespesaFilterSet(FilterSet):
    """
    Filtro para despesas.
    """
    ano_i = MultipleChoiceFilter(
        required=False,
        field_name='ano',
        label=_('Anos com LOA Registradas'),
        choices=choice_anos_loa(),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por um ou mais anos de LOA?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Anos da LOA',
            'data-dropup-auto': 'false'
        })
    )

    class Meta:
        model = Despesa
        fields = {
        }

        class Form(forms.Form):
            crispy_field_template = (
                'ano',
            )

        form = Form

class DespesaYearTotalizeDashcard(Dashcard):
    """
    """
    chart_type = Dashcard.TYPE_HTML

    model = Loa

    render_filterset = False
    filterable = False

    def get_labels(self, request, queryset=None):
        return [
            _('Valor Total de Despesas por Ano'),
        ]

    def get_datasets(self):
        return [
            {
                'label': _('Valor Total de Despesas'),
                'data_field': ('despesa_set__valor_materia', Sum),
            }
        ]



class LoaDashboardView(GridDashboard, TemplateView):
    """
    Dashboard para Leis Orçamentárias Anuais (LOA).
    """
    app_config = 'loa'
    container_css_class = 'container-fluid'

    filterset = DespesaFilterSet

    cards = [
        DespesaYearTotalizeDashcard
    ]

    grid = {
        'rows': [
            {
                'cols': [
                    ('DespesaYearTotalizeDashcard', 12),
                ]
            }
        ],
    }


    def get_template_names(self):
        return ['dashboard/loa/loa_dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Dashboard de Leis Orçamentárias Anuais (LOA)')
        return context
