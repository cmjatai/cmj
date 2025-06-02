
import re

from django import forms
from cmj.dashboard import Dashcard, GridDashboard
from django.db.models import Count
from sapl.materia.forms import CHOICE_TRAMITACAO
from sapl.materia.models import AssuntoMateria, MateriaLegislativa, StatusTramitacao, TipoMateriaLegislativa, UnidadeTramitacao
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView
from django_filters import FilterSet, CharFilter, ChoiceFilter, ModelMultipleChoiceFilter, MultipleChoiceFilter
from django.views.generic import TemplateView

from sapl.utils import choice_anos_com_materias

class MateriaFilterSet(FilterSet):

    tipo_i = ModelMultipleChoiceFilter(
        required=False,
        field_name='tipo',
        queryset=TipoMateriaLegislativa.objects.all(),
        label=_('Tipos de Matéria Legislativa'),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por um ou mais tipos de matéria?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Tipos de Matéria Legislativa',
            'data-dropup-auto': 'false'
        })
    )

    ano_i = MultipleChoiceFilter(
        required=False,
        field_name='ano',
        label=_('Anos das Matérias'),
        choices=choice_anos_com_materias(),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por um ou mais anos de matéria?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Anos de Matéria Legislativa',
            'data-dropup-auto': 'false'
        })
    )


    assuntos_is = ModelMultipleChoiceFilter(
        required=False,
        field_name='materiaassunto__assunto',
        queryset=AssuntoMateria.objects.all(),
        label=_('Assuntos'),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por um ou mais Assuntos?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Assuntos',
            'data-dropup-auto': 'false',
            'data-dropdown-align-right': 'auto'
        })
    )

    em_tramitacao_b = ChoiceFilter(
        required=False,
        field_name='em_tramitacao',
        label=_('Em tramitação'),
        choices=CHOICE_TRAMITACAO
    )

    autoria_is = CharFilter(
        required=False,
        field_name='autoria__autor',
        widget=forms.HiddenInput(attrs={'id': 'id_autoria__autor'}))

    uta_i = ModelMultipleChoiceFilter(
        required=False,
        field_name='materiaemtramitacao__tramitacao__unidade_tramitacao_destino',
        queryset=UnidadeTramitacao.objects.all(),
        label=_('Unidade de tramitação atual'),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por uma ou mais unidades?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Unidade de tramitação atual',
            'data-dropup-auto': 'false'
        })
    )

    sta_i = ModelMultipleChoiceFilter(
        required=False,
        field_name='materiaemtramitacao__tramitacao__status',
        queryset=StatusTramitacao.objects.all(),
        label=_('Status da tramitação atual'),
        widget=forms.SelectMultiple(attrs={
            'title': _('Filtrar por um ou mais Status?'),
            'class': 'selectpicker',
            'data-actions-box': 'true',
            'data-select-all-text': 'Selecionar Todos',
            'data-deselect-all-text': 'Desmarcar Todos',
            'data-header': 'Status da tramitação atual',
            'data-dropup-auto': 'false',
            'data-dropdown-align-right': 'auto'
        })
    )

    class Meta:
        model = MateriaLegislativa
        fields = {
        }


class MateriaTotalizer(Dashcard):
    title = _('Total de Matérias Legislativas')
    chart_type = Dashcard.TYPE_HTML
    model = MateriaLegislativa
    label_field = "id", Count

    render_filterset = False
    filterable = False

    datasets = [
        {
            "label": _("Qtd. de Matérias Legislativas"),
            "data_field": ("id", Count)
        }
    ]

    def get_datasets(self, request, queryset=None):
        return [
            {
                "data": [
                    queryset.count()
                    ]
            }
        ]

    def get_labels(self, request, queryset=None):
        return []
        return ['{}'.format(self.label_name)]

class MateriaTotalizerFiltered(MateriaTotalizer):
    title = _('Total de Matérias com a seleção atual')
    chart_type = Dashcard.TYPE_HTML
    model = MateriaLegislativa
    label_field = "id", Count

    render_filterset = False
    filterable = True

class MateriaDashboard(Dashcard):
    title = _('Distribuição por Assunto')
    description = _('Distribuição de Matérias por assunto')
    chart_type = Dashcard.TYPE_BAR
    model = MateriaLegislativa
    label_field = "assuntos__assunto"
    label_name = _("Assuntos")

    render_filterset = False

    datasets = [
        {
        "label": _("Qtd. de Matérias para o Assunto"),
        "data_field": ("assuntos", Count)
        }
    ]
    chart_options = {
        "scales": {"x": {"stacked": True}, "y": {"stacked": True}},
        "plugins": {"tooltip": {"mode": "index"}},
    }

    def get_datasets(self, request, queryset=None):
        ds = super().get_datasets(request, queryset)

        return ds

    def get_labels(self, request, queryset=None):
        labels = super().get_labels(request, queryset)

        return labels

    def chartdata(self, request, queryset=None):
        cd =  super().chartdata(request, queryset)

        labels = cd['data']['labels']
        datasets__data = cd['data']['datasets'][0]['data']

        # Sort the labels and datasets__data by datasets__data
        sorted_data = sorted(zip(labels, datasets__data), key=lambda x: x[1], reverse=True)
        if sorted_data:
            labels, datasets__data = zip(*sorted_data)

        # agrupa os dados da posição 20 em diante
        if len(labels) > 20:
            labels = list(labels[:20]) + ['Outros']
            datasets__data = list(datasets__data[:20]) + [sum(datasets__data[20:])]
        else:
            labels = list(labels)
            datasets__data = list(datasets__data)


        # Update the chart data with sorted values
        cd['data']['labels'] = labels
        cd['data']['datasets'][0]['data'] = datasets__data

        return cd


class MateriaSearchDashboard(GridDashboard):

    app_config = 'materia'
    cards = [
        MateriaTotalizer,
        MateriaTotalizerFiltered,
        MateriaDashboard,
    ]

    grid = {
        'rows': [
            {
                'cols': [
                    ('materiatotalizer', 6),
                    ('materiatotalizerfiltered', 6),
                    ('materiadashboard', 12),
                ]
            }
        ]
    }

class MateriaDashboardView(GridDashboard, TemplateView):

    app_config = 'materia'
    cards = [
        MateriaTotalizer,
        MateriaTotalizerFiltered,
        MateriaDashboard,
    ]

    filterset = MateriaFilterSet

    grid = {
        'rows': [
            {

                'cols': [
                    ('__filter__', 3),
                    (
                        {
                            'rows': [
                                {
                                    'cols': [
                                        ('materiatotalizer', 6),
                                        ('materiatotalizerfiltered', 6),
                                        ('materiadashboard', 12),
                                    ]
                                }
                            ]
                        }, 9
                    )
                ]
            },
        ]
    }

    def get_template_names(self):
        return ['dashboard/materia/materia_search_dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Dashboard de Matérias Legislativas')
        return context
