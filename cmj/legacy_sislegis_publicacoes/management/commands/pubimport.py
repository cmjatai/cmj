
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
import urllib3

from cmj.core.models import AreaTrabalho
from cmj.legacy_sislegis_publicacoes.models import Tipodoc, Tipolei, Documento
from sapl.protocoloadm.models import TipoDocumentoAdministrativo


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):

        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.run()
        # self.reset_id_model(DocumentoAdministrativo)

    def reset_id_model(self, model):

        query = """SELECT setval(pg_get_serial_sequence('"%(app_model_name)s"','id'),
                    coalesce(max("id"), 1), max("id") IS NOT null) 
                    FROM "%(app_model_name)s";
                """ % {
            'app_model_name': _get_registration_key(model)
        }

        with connection.cursor() as cursor:
            cursor.execute(query)
            # get all the rows as a list
            rows = cursor.fetchall()
            print(rows)

    def run(self):
        at = AreaTrabalho.objects.get(pk=22)

        tl_tda = {
            '25': ('PD', 'Publicações Diversas'),
        }

        tds = Tipodoc.objects.filter(ordem__gt=0).order_by('ordem')
        for td in tds:
            print(td.id, td.ordem, td.descr)

            tls = Tipolei.objects.filter(idtipodoc=td).order_by('ordem')

            for tl in tls:
                print('---- tl:', tl.id, tl.ordem, tl.descr)
                id_str = str(tl.id)
                if id_str in tl_tda:
                    tl_tda[id_str] = TipoDocumentoAdministrativo.objects.get_or_create(
                        sigla=tl_tda[id_str][0], descricao=tl_tda[id_str][1]
                    )
                    
                    
        for id_tipolei_id in tl_tda
        d_25 = Documento.objects.filter(id_tipolei_id=25)

        print('--------------------')
        print(d_25.count())
