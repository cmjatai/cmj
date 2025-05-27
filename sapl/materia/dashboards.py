
from dashboard.dashboard import Dashcard
from django.db.models import Count
from sapl.materia.models import MateriaLegislativa
from django.utils.translation import gettext_lazy as _

from django_filters import FilterSet, ChoiceFilter

from sapl.utils import choice_anos_com_materias

class MateriaFilterSet(FilterSet):

    ano = ChoiceFilter(
        required=False,
        label='Ano das Matérias',
        choices=choice_anos_com_materias)

    class Meta:
        model = MateriaLegislativa
        fields = {
            'ano': ['exact', ],
        }


class MateriaTotalizer: #(Dashcard):
    title = _('Total de Matérias Legislativas')
    chart_type = Dashcard.TYPE_HTML
    model = MateriaLegislativa
    label_field = "id", Count
    label_name = _("Requerimentos")

    filterset = MateriaFilterSet

    datasets = [
        {
            "label": _("Qtd. de Requerimentos"),
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
        return ['{}'.format(self.label_name)]

class MateriaDashboard(Dashcard):
    title = _('Distribuição de Requerimentos por Assunto')
    description = _('Distribuição de Requerimentos por assunto')
    chart_type = Dashcard.TYPE_BAR
    model = MateriaLegislativa
    label_field = "assuntos__assunto"
    label_name = _("Assuntos")

    datasets = [
        {
        "label": _("Qtd. de Requerimentos para o Assunto"),
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