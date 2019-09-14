from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete, post_save
from sapl.materia.models import DocumentoAcessorio, TipoDocumento
from sapl.protocoloadm.models import DocumentoAdministrativo


class Command(BaseCommand):
    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.run()

    def run(self):

        pareceres = DocumentoAcessorio.objects.filter(tipo_id=1)

        # for p in pareceres:
        #    print(p)

        docs = DocumentoAdministrativo.objects.exclude(numero_externo=None)
        print(docs.count())

        for d in docs:
            print(d.id, d.assunto, d.numero_externo)
