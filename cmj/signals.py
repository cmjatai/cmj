from celery_haystack.signals import CelerySignalProcessor
from cmj.sigad.models import Documento


class CelerySignalProcessor(CelerySignalProcessor):

    def enqueue_save(self, sender, instance, **kwargs):
        action = 'update'
        if isinstance(instance, Documento):
            if instance.visibilidade != Documento.STATUS_PUBLIC:
                action = 'delete'

        return self.enqueue(action, instance, sender, **kwargs)

    def enqueue_delete(self, sender, instance, **kwargs):
        return self.enqueue('delete', instance, sender, **kwargs)
