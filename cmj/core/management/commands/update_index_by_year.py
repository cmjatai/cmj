from time import sleep
import logging

from django.core import management
from django.core.management.base import BaseCommand

from cmj.arq.models import ArqDoc
from cmj.diarios.models import DiarioOficial
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import SessaoPlenaria


class Command(BaseCommand):
    models = [
        {
            'model': DocumentoAdministrativo,
            'last_updated': 'data_ultima_atualizacao',
            'using': 'default'
        },
        {
            'model': MateriaLegislativa,
            'last_updated': 'data_ultima_atualizacao',
            'using': 'default'
        },
        {
            'model': NormaJuridica,
            'last_updated': 'data_ultima_atualizacao',
            'using': 'default'
        },
        {
            'model': DocumentoAcessorio,
            'last_updated': 'data_ultima_atualizacao',
            'using': 'default'
        },
        {
            'model': SessaoPlenaria,
            'last_updated': 'data_ultima_atualizacao',
            'using': 'default'
        },
        {
            'model': DiarioOficial,
            'last_updated': 'data_ultima_atualizacao',
            'using': 'default'
        },
        {
            'model': ArqDoc,
            'last_updated': 'modified',
            'using': 'cmjarq'
        },
    ]

    def handle(self, *args, **options):


        self.logger = logging.getLogger(__name__)

        years_updated = set()

        for model in self.models:
            m = model['model']
            years_updated = model['model'].objects.values_list(
                f'{model["last_updated"]}__year', flat=True
            ).order_by(
                f'{model["last_updated"]}__year'
            ).distinct()
            for y in years_updated:
                try:
                    self.logger.info(
                        f'Ano Executado: {y} chamando update_index...')
                    params = [
                        'update_index',
                        f"{m._meta.app_label}.{m._meta.object_name}",
                        f"--start={y}-01-01T00:00:00'",
                        f"--end='{y}-12-31T23:59:59'",
                        '--verbosity=3',
                        '--batch-size=100',
                        f"--using={model['using']}"
                        ]
                    management.call_command(*params)
                    sleep(60)
                except Exception as e:
                    self.logger.error(e)

