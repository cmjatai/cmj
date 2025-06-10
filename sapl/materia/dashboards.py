
from collections import OrderedDict
import re
import sys

from django import forms
from cmj.dashboard import Dashcard, GridDashboard
from django.db.models import Count, F, Q
from django.db.models.functions import TruncMonth
from sapl.base.models import Autor
from sapl.crispy_layout_mixin import to_row
from sapl.materia.forms import CHOICE_TRAMITACAO
from sapl.materia.models import AssuntoMateria, MateriaLegislativa, StatusTramitacao, TipoMateriaLegislativa, UnidadeTramitacao
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView
from django_filters import FilterSet, CharFilter, ChoiceFilter, ModelChoiceFilter, ModelMultipleChoiceFilter, MultipleChoiceFilter
from django.views.generic import TemplateView
from django.utils import timezone
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout, HTML, Button, Fieldset

from sapl.utils import RangeWidgetNumber, choice_anos_com_materias, autor_label, \
    autor_modal, choice_anos_com_normas

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

    autoria_is = ModelChoiceFilter(
        required=False,
        field_name='autoria__autor',
        queryset=Autor.objects.all(),
        widget=forms.HiddenInput(attrs={'id': 'id_autoria__autor'})
    )

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

        class Form(forms.Form):
            crispy_field_template = (
                'tipo_i',
                'ano_i',
                'assuntos_is',
                'em_tramitacao_b',
                'autoria_is',
                'sta_i',
                'uta_i',
            )
        form = Form

        fields = {
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        row1 = to_row([
            ('tipo_i', 12),
            ('em_tramitacao_b', 6),
            ('ano_i', 6),
        ])

        row2 = to_row([
            ('uta_i', 12),
            ('sta_i', 12),
        ])

        row3 = to_row([
            ('assuntos_is', 12),
            (Div(
                HTML(autor_label),
                HTML(autor_modal),
                to_row([
                    ('autoria_is', 0),
                    (Button('pesquisar',
                            'Selecionar Autor',
                            css_class='btn btn-secondary btn-sm mt-1 w-100'), 12),
                    (Button('limpar',
                            'Limpar Autor',
                            css_class='btn btn-secondary btn-sm mt-1 p-0 w-100'), 12),
                ], css_class='row flex-column'),
                css_class="form-group"
            ), 6),
        ])

        self.form.helper = FormHelper()
        self.form.helper.form_tag = False
        self.form.helper.layout = Layout(
                     row1,
                     row2,
                     row3)


        return
        grupos_de_tipos = (
            ('1', 'Mais Acessadas'),
            ('3', ' '),
            ('7', 'Matérias Acessórias'),
            ('9', '  ')
        )
        gtd = dict(grupos_de_tipos)  # {k: v for k, v in grupos_de_tipos}

        grupo_choices = OrderedDict()
        for nivel, valor in grupos_de_tipos:
            if valor not in grupo_choices:
                grupo_choices[valor] = []

        for tml in TipoMateriaLegislativa.objects.order_by('nivel_agrupamento', 'sequencia_regimental'):
            grupo_choices[gtd[tml.nivel_agrupamento]].append(
                (tml.id, f'{tml.sigla} - {tml.descricao}'))

        choices = []
        for g, items in grupo_choices.items():
            choices.append((' ', items,))
        self.form.fields['tipo_i'].choices = choices

        uta_choices = OrderedDict()
        for uta in UnidadeTramitacao.objects.filter(
            ativo=True,
            # tramitacoes_destino__isnull=False
            materiasemtramitacao_set__isnull=False
            ).order_by('comissao', 'orgao', 'parlamentar').distinct():
            uta_obj = uta.comissao or uta.orgao or uta.parlamentar

            grupo = uta_obj._meta.verbose_name_plural
            if grupo not in uta_choices:
                uta_choices[grupo] = []

            uta_choices[grupo].append((uta.id, str(uta)))

        self.form.fields['uta_i'].choices = uta_choices.items()


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

class OrderedResultMixin:

    def chartdata(self, request, queryset=None, limit=20):
        cd =  super().chartdata(request, queryset)

        labels = cd['data']['labels']
        datasets__data = cd['data']['datasets'][0]['data']

        # Sort the labels and datasets__data by datasets__data
        sorted_data = sorted(
            filter(
                lambda y: y[0],
                zip(labels, datasets__data)
            ),
            key=lambda x: x[1],
            reverse=True
            )
        if sorted_data:
            labels, datasets__data = zip(*sorted_data)

        # agrupa os dados da posição 20 em diante
        if len(labels) > limit:
            labels = list(labels[:limit]) + ['Outros']
            datasets__data = list(datasets__data[:limit]) + [sum(datasets__data[limit:])]
        else:
            labels = list(labels)
            datasets__data = list(datasets__data)


        # Update the chart data with sorted values
        cd['data']['labels'] = labels
        cd['data']['datasets'][0]['data'] = datasets__data

        return cd

class MateriaDashboard(OrderedResultMixin, Dashcard):
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
    #chart_options = {
    #    "scales": {"x": {"stacked": True}, "y": {"stacked": True}},
    ##    "plugins": {"tooltip": {"mode": "index"}},
    #}

    def get_datasets(self, request, queryset=None):
        ds = super().get_datasets(request, queryset)

        return ds

    def get_labels(self, request, queryset=None):
        labels = super().get_labels(request, queryset)

        return labels


class MateriaMonthlyDashboard(Dashcard):
    title = _('Distribuição Mensal de Matérias')
    description = _('Distribuição de Matérias por mês')
    chart_type = Dashcard.TYPE_BAR
    model = MateriaLegislativa
    label_field = ("data_apresentacao", TruncMonth, lambda d: d.strftime("%m/%Y"))

    render_filterset = False

    style="height: 40vh;"

    datasets = [
        {
            "label": _("Qtd. de Matérias por Mês"),
            "type": Dashcard.TYPE_BAR,
            "data_field": ("*", Count)
        },
        {
            "label": _("Tendência"),
            "type": Dashcard.TYPE_LINE,
            "data_field": ("*", Count),
            "tension": 0.3,
            "pointStyle": False
        }
    ]
    chart_options = {
        "maintainAspectRatio": False,
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.GET.getlist('ano_i'):
            now = timezone.now()
            qs = qs.filter(data_apresentacao__year__gt=now.year-9)
        return qs

    def get_datasets(self, request, queryset=None):
        ds = super().get_datasets(request, queryset)

        data_line = ds[1]['data']
        # para cada elemento de data_line, calcula a média do início até o elemento atual

        periodo = 12
        new_data_line = [0] * len(data_line)
        for i, v in enumerate(data_line):
            if i >= periodo:
                # calcula a média dos últimos 12 meses
                new_data_line[i] = sum(data_line[i-periodo:i]) / periodo
            else:
                new_data_line[i] = sum(data_line[:i+1]) / (i+1) if i > 0 else v

        ds[1]['data'] = new_data_line

        return ds

    def get_labels(self, request, queryset=None):
        labels = super().get_labels(request, queryset)

        return labels


class MateriaSearchDashboard(GridDashboard):

    app_config = 'materia'
    cards = [
        MateriaTotalizer,
        MateriaTotalizerFiltered,
        MateriaMonthlyDashboard,
        MateriaDashboard,
    ]

    grid = {
        'rows': [
            {
                'cols': [
                    ('materiatotalizer', 6),
                    ('materiatotalizerfiltered', 6),
                    ('materiamonthlydashboard', 12),
                    ('materiadashboard', 12),
                ]
            }
        ]
    }


class MateriaParlamentarDashboard(GridDashboard):

    app_config = 'materia'
    cards = [
        MateriaMonthlyDashboard,
        MateriaTotalizerFiltered
    ]

    class AutoriaFilterSet(FilterSet):


        autoria_is = CharFilter(
            required=False,
            field_name='autoria__autor',
            widget=forms.HiddenInput(attrs={'id': 'id_autoria__autor'})
        )

        class Meta:
            model = MateriaLegislativa
            fields = {
            }

        def get_queryset(self, queryset=None):
            if not queryset:
                queryset = super().get_queryset()
            return queryset

    render_filterset = True
    filterset = AutoriaFilterSet

    grid = {
        'rows': [
            {
                'cols': [
                    ('__filter__', 12),
                    ('materiatotalizerfiltered', 12),
                    ('materiamonthlydashboard', 12),
                ]
            }
        ]
    }

class PartidoDashboard(OrderedResultMixin, Dashcard):
    title = _('Distribuição de Matérias por Partido')
    description = _('Distribuição de Matérias por partido')
    chart_type = Dashcard.TYPE_BAR
    model = MateriaLegislativa
    label_field = "autoria__autor__parlamentar_set__filiacao__partido__sigla"
    label_name = _("Partidos")
    style="height: 40vh;"

    render_filterset = False

    datasets = [
        {
            "label": _("Qtd. de Matérias por Partido"),
            "data_field": ("autoria__autor__parlamentar_set__filiacao__partido__sigla", Count)
        }
    ]
    chart_options = {
        "maintainAspectRatio": False,
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        q = Q(
            autoria__autor__parlamentar_set__filiacao__data_desfiliacao__isnull=True,
            data_apresentacao__gte=F('autoria__autor__parlamentar_set__filiacao__data')
            ) | Q(
            data_apresentacao__range=(
                F('autoria__autor__parlamentar_set__filiacao__data'),
                F('autoria__autor__parlamentar_set__filiacao__data_desfiliacao')
            )
        )
        q = q & Q(
            autoria__autor__parlamentar_set__filiacao__partido__sigla__isnull=False
        )

        qs = qs.filter(q)
        #    #autoria__autor__parlamentar_set__filiacao__data_desfiliacao__isnull=True,
        #    #autoria__autor__parlamentar_set__ativo=True
        #)
        qs = qs.order_by(
            'id',
            ).distinct()
        return qs

    def get_datasets(self, request, queryset=None):
        ds = super().get_datasets(request, queryset)
        # agrupamento do dataset incorreto se autor for selecionado
        return ds

    def chartdata(self, request, queryset=None, limit=20):
        cd = super().chartdata(request, queryset, limit)

        data = request.GET.get('autoria_is', {}) if hasattr(request, 'GET') else request

        autor_id = data if isinstance(data, str) else data.get('autoria_is', None)
        if not autor_id:
            return cd

        autor = Autor.objects.filter(id=autor_id).first()
        if not autor:
            return cd

        filiacoes = autor.parlamentar_set.values_list(
            'filiacao__partido__sigla',
            'filiacao__parlamentar',
            'filiacao__data',
            'filiacao__data_desfiliacao'
        ).distinct()

        if not filiacoes:
            return cd

        # filtra os dados do dataset para incluir apenas as matérias do autor
        labels = cd['data']['labels']
        datasets__data = cd['data']['datasets'][0]['data']
        filtered_labels = []
        filtered_data = []
        qs = queryset or self.get_queryset(request)
        for label, data in zip(labels, datasets__data):

            for f in filiacoes:
                if f[0] != label:
                    continue

                q = Q(
                    autoria__autor=autor,
                    data_apresentacao__range=(f[2], f[3] or timezone.now())
                )
                qs_partido = qs.filter(q)

                filtered_labels.append(label)
                filtered_data.append(qs_partido.count())

        cd['data']['labels'] = filtered_labels
        cd['data']['datasets'][0]['data'] = filtered_data

        return cd

class MateriaDashboardView(GridDashboard, TemplateView):

    app_config = 'materia'
    cards = [
        MateriaTotalizer,
        MateriaTotalizerFiltered,
        MateriaMonthlyDashboard,
        MateriaDashboard,
        PartidoDashboard,
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
                                        ('materiatotalizerfiltered', 6),
                                        ('materiatotalizer', 6),
                                        ('materiamonthlydashboard', 6),
                                        ('partidodashboard', 6),
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
