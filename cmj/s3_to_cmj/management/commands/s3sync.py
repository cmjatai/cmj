
from django.db.models.signals import post_save, post_delete
from sapl.rules.apps import sapl_post_delete_signal, sapl_post_save_signal

from cmj.globalrules.apps import cmj_post_delete_signal, cmj_post_save_signal
from cmj.s3_to_cmj.management.commands import s3import
from cmj.s3_to_cmj.migracao_documentos_via_request import migrar_docs_por_ids


class Command(s3import.Command):
    sync = None

    def add_arguments(self, parser):
        parser.add_argument('sync', nargs='?', type=float, default=None)

    def handle(self, *args, **options):
        post_delete.disconnect(sapl_post_delete_signal)
        post_save.disconnect(sapl_post_save_signal)
        post_delete.disconnect(cmj_post_delete_signal)
        post_save.disconnect(cmj_post_save_signal)

        self.sync = options['sync']
        self.run()
        self.reset_sequences()
        self.migrar_documentos()
        # self.list_models_with_relation()

    def migrar_docs_por_ids(self, model):
        return migrar_docs_por_ids(model, self.sync)
