
from dashboard import Dashcard
from django.db.models import Count
from sapl.materia.models import MateriaLegislativa
from django.utils.translation import gettext_lazy as _


class MateriaDashboard(Dashcard):
    title = _('Distribuição das Matérias por Assunto')
    description = _('Distribuição das matérias por assunto')
    chart_type = Dashcard.TYPE_BAR
    model = MateriaLegislativa
    label_field = "assuntos__assunto"
    label_name = _("Assuntos")

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
    """chart_options = {
        "legend": {
            "display": True,
            "position": "right",
            "labels": {
                "fontSize": 12,
                "padding": 20
            }
        },
        "title": {
            "display": True,
            "text": 'Distribuição das Matérias por Assunto',
            "fontSize": 16,
            "padding": 20
        },
        "responsive": True,
        "maintainAspectRatio": False,
        "aspectRatio": 1,
        "cutoutPercentage": 70,
        "animation": {
            "animateScale": True,
            "animateRotate": True
        },
        "tooltips": {
            "enabled": True,
            "mode": 'index',
            "intersect": False,
            "callbacks": {
                "label": lambda tooltipItem, data: f"{data['labels'][tooltipItem['index']]}: {tooltipItem['yLabel']}"
            }
        }
    }"""

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