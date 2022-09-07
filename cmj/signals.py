import logging

from asgiref.sync import async_to_sync
from celery_haystack.signals import CelerySignalProcessor
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver

from cmj.sigad.models import Documento

logger = logging.getLogger(__name__)


class CelerySignalProcessor(CelerySignalProcessor):

    def enqueue_save(self, sender, instance, **kwargs):
        action = 'update'
        if isinstance(instance, Documento):
            if instance.visibilidade != Documento.STATUS_PUBLIC:
                action = 'delete'

        return self.enqueue(action, instance, sender, **kwargs)

    def enqueue_delete(self, sender, instance, **kwargs):
        return self.enqueue('delete', instance, sender, **kwargs)


def send_signal_for_websocket_time_refresh(project, action, inst):
    if not settings.USE_CHANNEL_LAYERS:
        return

    if hasattr(inst, '_meta') and not inst._meta.app_config is None and \
            inst._meta.app_config.name[:4] == project:

        try:
            if hasattr(inst, 'ws_sync') and not inst.ws_sync():
                return

            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                "group_time_refresh_channel", {
                    "type": "time_refresh.message",
                    'message': {
                        'action': action,
                        'id': inst.id,
                        'app': inst._meta.app_label,
                        'model': inst._meta.model_name
                    }
                }
            )
        except Exception as e:
            logger.info(_("Erro na comunicação com o backend do redis. "
                          "Certifique se possuir um servidor de redis "
                          "ativo funcionando como configurado em "
                          "CHANNEL_LAYERS"))


@receiver(post_save, dispatch_uid='sapl_post_save_signal')
def sapl_post_save_signal(sender, instance, using, **kwargs):
    send_signal_for_websocket_time_refresh('sapl', 'post_save', instance)


@receiver(post_delete, dispatch_uid='sapl_post_delete_signal')
def sapl_post_delete_signal(sender, instance, using, **kwargs):
    send_signal_for_websocket_time_refresh('sapl', 'post_delete', instance)
