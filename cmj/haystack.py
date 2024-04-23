
import logging

from celery_haystack.signals import CelerySignalProcessor
from django.core import serializers
from django.db.models.base import Model
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

        update_fields = kwargs.get('update_fields', []) or []
        if 'checkcheck' in update_fields and len(update_fields) == 1:
            return

        return self.enqueue(action, instance, sender, **kwargs)

    def enqueue_delete(self, sender, instance, **kwargs):
        return self.enqueue('delete', instance, sender, **kwargs)


class CmjDefaultRouter(DefaultRouter):

    def for_write(self, **hints):
        return self.for_rw(**hints)

    def for_read(self, **hints):
        return self.for_rw(**hints)

    def for_rw(self, **hints):
        # logger.debug(hints)
        if not hints:
            return DEFAULT_ALIAS

        if 'instance' in hints:
            m = hints['instance']._meta.model
            if m in MODELS_SOLR_CMJARQ:
                return CMJARQ_ALIAS
            elif m not in MODELS_SOLR_DEFAULT:
                return None
        elif 'index' in hints:
            m = hints['index'].model
            if m in MODELS_SOLR_CMJARQ:
                return CMJARQ_ALIAS
            elif m not in MODELS_SOLR_DEFAULT:
                return None
        elif 'models' in hints:
            m = hints['models']
            if m and not isinstance(m, Model):
                m = m[0]
            if m in MODELS_SOLR_CMJARQ:
                return CMJARQ_ALIAS
            elif m not in MODELS_SOLR_DEFAULT:
                return None
        return DEFAULT_ALIAS
