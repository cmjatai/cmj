from django.db.models.signals import post_delete, post_save

from cmj.s3_to_cmj.management.commands import s3import
from cmj.s3_to_cmj.migracao_documentos_via_request import migrar_docs_por_ids


class Command(s3import.Command):
    sync = None
    migrate_files = False

    def add_arguments(self, parser):
        parser.add_argument('sync', nargs='?', type=float, default=None)
        parser.add_argument('f', nargs='?', type=bool, default=False)

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')
        # post_delete.disconnect(sapl_post_delete_signal)
        # post_save.disconnect(sapl_post_save_signal)
        # post_delete.disconnect(cmj_post_delete_signal)
        # post_save.disconnect(cmj_post_save_signal)

        self.sync = options['sync']
        self.migrate_files = options['f']

        self.run()
        self.reset_sequences()

        if self.migrate_files:
            self.migrar_documentos()

        # self.list_models_with_relation()

    def migrar_docs_por_ids(self, model):
        return migrar_docs_por_ids(model, self.sync)
