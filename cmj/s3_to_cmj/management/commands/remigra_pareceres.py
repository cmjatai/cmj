import re

from django.core.management.base import BaseCommand
from django.db.models import Q
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

        pareceres = DocumentoAcessorio.objects.filter(
            Q(autor__icontains='leonardo') | Q(
                autor__icontains='renata') | Q(autor__icontains='silmar'),
            tipo_id=1,
        )

        print(pareceres.count())

        count = 0
        for p in pareceres:
            m = re.match('([^0-9]+)([0-9]+)/ ?([0-9]+)', p.nome)
            if m:
                if 'projeto' not in p.nome and 'Proj.' not in p.nome:
                    pass
                else:
                    continue

            else:
                continue

            count += 1
            #print(p.id, p.nome)

            continue

            d = DocumentoAdministrativo.objects.filter(
                temp_migracao_doc_acessorio=p.id).first()

            if not d:
                d = DocumentoAdministrativo()
                d.temp_migracao_doc_acessorio = p.id
                d.materia = p.materia
                d.tipo_id = 150
                d.ano = p.data.year
                d.numero

        print(count)
