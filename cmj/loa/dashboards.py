

from django import forms
from django.http import JsonResponse
from cmj.dashboard.dashboard import Dashcard, GridDashboard
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from django.db.models import F
from cmj.loa.models import Despesa, Loa
from django.db.models import Sum, Value
from django_filters import FilterSet, CharFilter, ChoiceFilter, ModelChoiceFilter, ModelMultipleChoiceFilter, MultipleChoiceFilter

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout

from sapl.crispy_layout_mixin import to_row

def choice_anos_loa():
    return [(ano, str(ano)) for ano in Despesa.objects.values_list('loa__ano', flat=True).distinct().order_by('loa__ano')]

class DespesaFilterSet(FilterSet):
    """
    Filtro para despesas.
    """
    loa__ano = MultipleChoiceFilter(
        required=False,
        label=_('Anos com LOA Registradas'),
        choices=choice_anos_loa(),
        widget=forms.SelectMultiple()
    )

    class Meta:
        model = Despesa
        fields = {
        }

        class Form(forms.Form):
            crispy_field_template = (
                'loa__ano',
            )

        form = Form

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        row1 = to_row([
            ('loa__ano', 12),
        ])


        self.form.helper = FormHelper()
        self.form.helper.form_tag = False
        self.form.helper.layout = Layout(
                     row1,)


class DespesaYearTotalizeDashcard(Dashcard):
    chart_type = Dashcard.TYPE_BAR

    model = Despesa

    render_filterset = False
    filterable = True
    label_field = 'loa__ano'
    datasets = [
        {
            'label': _('Orçamento Geral Anual'),
            'data_field': ('valor_materia', Sum),
        },
        {
            'label': _('RCL - Receita Corrente Líquida'),
            'data_field': ('loa__receita_corrente_liquida', F, None, True),
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
                    ('__filter__', 4),
                    (
                        {
                            'rows': [
                                {
                                    'cols': [
                                        ('DespesaYearTotalizeDashcard', 12),
                                    ]
                                }
                            ]
                        }, 8),
                ]
            }
        ],
    }


    def get_template_names(self):
        # template para templateview
        return ['dashboard/loa/loa_dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Dashboard de Leis Orçamentárias Anuais (LOA)')
        return context

    def get(self, request, *args, **kwargs):
        grid = request.GET.get('grid', None)
        if grid is not None:
            return JsonResponse(self.grid, safe=False)
        return super().get(request, *args, **kwargs)
