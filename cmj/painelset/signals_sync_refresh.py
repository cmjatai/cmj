import logging
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from cmj.painelset import tasks, tasks_function


logger = logging.getLogger(__name__)


def send_signal_for_websocket_sync_refresh(inst, **kwargs):

    action = 'post_save' if 'created' in kwargs else 'post_delete'
    created = kwargs.get('created', False)

    if inst._meta.label in (
        'painelset.Evento',
        'painelset.Individuo',
        'painelset.Cronometro',
        'painelset.CronometroEvent',
        'painelset.Painel',
        'painelset.VisaoDePainel',
        'painelset.Widget',
        'sessao.SessaoPlenaria',
    ):

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
                "group_sync_refresh_channel", {
                    "type": "sync_refresh.message",
                    'message': message
                }
            )


            if not inst._meta.label in (
                    'painelset.VisaoDePainel',
                    'painelset.Cronometro',
                    'painelset.CronometroEvent',
                ):
                if not settings.DEBUG or (
                    settings.DEBUG and settings.FOLDER_DEBUG_CONTAINER == settings.PROJECT_DIR
                ):
                    countdown = 0 if hasattr(inst, 'com_a_palavra') and inst.com_a_palavra else 3
                    tasks.task_refresh_states_from_visaodepainel.apply_async(countdown=countdown)
                else:
                    tasks_function.task_refresh_states_from_visaodepainel_function()

        except Exception as e:
            logger.error(_("Erro na comunicação com o backend do redis. "
                           "Certifique se possuir um servidor de redis "
                           "ativo funcionando como configurado em "
                           "CHANNEL_LAYERS"))
