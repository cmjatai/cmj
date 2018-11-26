from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo

from cmj.s3_to_cmj import mapa
from cmj.s3_to_cmj.management.commands import s3import
from cmj.s3_to_cmj.migracao_documentos_via_request import migrar_docs_por_ids


class Command(s3import.Command):
    sync = None

    def add_arguments(self, parser):
        parser.add_argument('sync', nargs='?', type=float, default=None)

    def handle(self, *args, **options):
        self.sync = options['sync']
        self.run()
        self.reset_sequences()
        self.migrar_documentos()
        # self.list_models_with_relation()

    def migrar_docs_por_ids(self, model):
        return migrar_docs_por_ids(model, self.sync)
