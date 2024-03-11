
import logging

from celery_haystack.signals import CelerySignalProcessor
from haystack.constants import DEFAULT_ALIAS
from haystack.routers import DefaultRouter

from cmj.arq.models import ArqDoc
from cmj.diarios.models import DiarioOficial
from cmj.sigad.models import Documento
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo
from sapl.sessao.models import SessaoPlenaria


logger = logging.getLogger(__name__)

CMJARQ_ALIAS = 'cmjarq'

MODELS_SOLR_DEFAULT = (DiarioOficial,
                       Documento,
                       DocumentoAdministrativo,
                       DocumentoAcessorio,
                       MateriaLegislativa,
                       NormaJuridica,
                       SessaoPlenaria)

MODELS_SOLR_CMJARQ = (ArqDoc, )


class CelerySignalProcessor(CelerySignalProcessor):

    def enqueue_save(self, sender, instance, **kwargs):

        if sender not in (MODELS_SOLR_CMJARQ + MODELS_SOLR_DEFAULT):
            return

        action = 'update'
        if isinstance(instance, Documento):
            if instance.visibilidade != Documento.STATUS_PUBLIC:
                action = 'delete'

        return self.enqueue(action, instance, sender, **kwargs)

    def enqueue_delete(self, sender, instance, **kwargs):
        return self.enqueue('delete', instance, sender, **kwargs)


class CmjDefaultRouter(DefaultRouter):

    def for_write(self, **hints):
        return self.for_rw(**hints)

    def for_read(self, **hints):
        return self.for_rw(**hints)

    def for_rw(self, **hints):
        if not hints:
            return DEFAULT_ALIAS

        if 'instance' in hints:
            if hints['instance']._meta in MODELS_SOLR_CMJARQ:
                return CMJARQ_ALIAS
        elif 'index' in hints:
            if hints['index'].model._meta in MODELS_SOLR_CMJARQ:
                return CMJARQ_ALIAS
        return DEFAULT_ALIAS
