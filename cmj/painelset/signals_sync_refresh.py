import logging
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from cmj.painelset import tasks, tasks_function
import re

logger = logging.getLogger(__name__)

regex_applabels_permitidos = [
    r'^painelset',
    r'^sessao',
    r'^parlamentares',
    r'^materia',
    r'^base',
    r'^norma',
]
regex_applabels_permitidos = [re.compile(label) for label in regex_applabels_permitidos]

def send_signal_for_websocket_sync_refresh(inst, **kwargs):

    action = 'post_save' if 'created' in kwargs else 'post_delete'
    created = kwargs.get('created', False)

    if any(regex.match(inst._meta.label) for regex in regex_applabels_permitidos):
        if settings.DEBUG:
            logger.debug(f'start: {inst.id} {inst._meta.app_label}.{inst._meta.model_name}')

        try:
            if hasattr(inst, 'ws_sync') and not inst.ws_sync():
                return

            from drfautoapi.drfautoapi import ApiViewSetConstrutor

            inst_serialize = None
            if hasattr(inst, 'ws_serialize'):
                inst_serialize = inst.ws_serialize()

            message = {
                'action': action,
                'id': inst.id,
                'app': inst._meta.app_label,
                'model': inst._meta.model_name,
                'created': created,
                'timestamp': time.time() * 1000,
                'instance': None
            }
            try:
                if inst_serialize:
                    message['instance'] = inst_serialize
                else:
                    message['instance'] = ApiViewSetConstrutor.get_viewset_for_model(
                        inst._meta.model
                    ).serializer_class(inst).data
            except Exception as e:
                logger.error(_("Erro ao serializar instância para sync_refresh: {}").format(e))

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "group_sync_refresh_channel", {
                    "type": "sync_refresh.message",
                    'message': message
                }
            )

        except Exception as e:
            logger.error(_("Erro signals_sync_refresh: {}").format(e))
