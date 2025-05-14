

from dashboard import Dashcard
from django.db.models import Count
from sapl.materia.models import MateriaLegislativa


class MaterialDashboard(Dashcard):
    title = 'Distribuição das Matérias por Assunto'
    chart_type = Dashcard.TYPE_DOUGHNUT
    model = MateriaLegislativa
    label_field = "assuntos__assunto"
    datasets = [{"data_field": ("assuntos", Count)}]

