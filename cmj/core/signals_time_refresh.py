import logging
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)


def send_signal_for_websocket_time_refresh(inst, **kwargs):

    action = 'post_save' if 'created' in kwargs else 'post_delete'
    created = kwargs.get('created', False)

    if hasattr(inst, '_meta') and \
        not inst._meta.app_config is None and \
            inst._meta.app_config.name in settings.SAPL_APPS:

        if settings.DEBUG:
            logger.debug(f'start: {inst.id} {inst._meta.app_label}.{inst._meta.model_name}')

        try:
            if hasattr(inst, 'ws_sync') and not inst.ws_sync():
                return

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
            if inst_serialize:
                message['instance'] = inst_serialize

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "group_time_refresh_channel", {
                    "type": "time_refresh.message",
                    'message': message
                }
            )

        except Exception as e:
            logger.error(_("Erro na comunicação com o backend do redis. "
                           "Certifique se possuir um servidor de redis "
                           "ativo funcionando como configurado em "
                           "CHANNEL_LAYERS"))
