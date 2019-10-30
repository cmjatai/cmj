from datetime import datetime
import logging

from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.db.models.signals import post_delete, post_save

from sapl.compilacao.models import TextoArticulado, Dispositivo
from sapl.protocoloadm.models import DocumentoAdministrativo


class Command(BaseCommand):

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        self.run_ajusta_datas_de_edicao_com_certidoes()
        
    def run_ajusta_datas_de_edicao_com_certidoes(self):
        
        # Área de trabalho pública
        docs = DocumentoAdministrativo.objects.filter(workspace_id=22).order_by('-data')
        
        for d in docs:
            c = d.certidao
            
            if not c:
                continue
            
            
            
            print(c.created, d.epigrafe)
        
        

    def run_ordene_dispositivos_pelos_numeros(self):
        init = datetime.now()

        ta = TextoArticulado.objects.get(pk=1121)

        dpts = Dispositivo.objects.filter(ta=self)

        if not dpts.exists():
            return

        ordem_max = dpts.last().ordem
        dpts.update(ordem=F('ordem') + ordem_max)

        raizes = Dispositivo.objects.filter(
            ta=self,
            dispositivo_pai__isnull=True).values_list(
                'pk', flat=True).order_by('ordem')
