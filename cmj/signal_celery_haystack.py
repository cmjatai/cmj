
import logging

from celery_haystack.signals import CelerySignalProcessor

from cmj.diarios.models import DiarioOficial
from cmj.sigad.models import Documento
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import SessaoPlenaria


logger = logging.getLogger(__name__)


class CelerySignalProcessor(CelerySignalProcessor):

    def enqueue_save(self, sender, instance, **kwargs):

        if sender not in (DiarioOficial,
                          Documento,
                          DocumentoAdministrativo,
                          DocumentoAcessorio,
                          MateriaLegislativa,
                          NormaJuridica,
                          SessaoPlenaria):
            return

        action = 'update'
        if isinstance(instance, Documento):
            if instance.visibilidade != Documento.STATUS_PUBLIC:
                action = 'delete'

        return self.enqueue(action, instance, sender, **kwargs)

    def enqueue_delete(self, sender, instance, **kwargs):
        return self.enqueue('delete', instance, sender, **kwargs)
