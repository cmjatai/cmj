import json
import time

from channels.generic.websocket import AsyncWebsocketConsumer
from click import command
from django.utils import timezone
from channels.db import database_sync_to_async
import logging
logger = logging.getLogger(__name__)

class TimeRefreshConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        from sapl.api.permissions import portalcmj_rpp
        self.portalcmj_rpp = portalcmj_rpp

        #print('Conectando ao TimeRefreshConsumer')
        self.room_name = 'time_refresh_channel'
        self.room_group_name = 'group_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        #print('Desconectando do TimeRefreshConsumer')
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        jdata = json.loads(text_data)

        type_msg = jdata.get('type', '')
        timestamp = jdata.get('timestamp_client', '')

        if type_msg == 'ping' and timestamp:
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp_server': time.time(), # timezone.now().timestamp(),
                'timestamp_client': timestamp
            }))

    # Receive message from room group
    async def time_refresh_message(self, event):

        try:

            message = event['message']
            app = message.get('app')
            model = message.get('model')

            u = self.scope.get('user')

            key = f"{app}:{model}"
            perms_publicas = self.portalcmj_rpp.get(key, set())

            perm_detail = f"{app}.detail_{model}"
            perm_view = f"{app}.view_{model}"

            if u.is_anonymous and not perms_publicas:
                detail_perm = False
            elif u.is_anonymous:
                detail_perm = perm_detail in perms_publicas or perm_view in perms_publicas
            elif not u.is_superuser:
                detail_perm = u.has_perm(perm_detail) or u.has_perm(perm_view)
            else:
                detail_perm = True

            try:
                if not detail_perm:
                    del message['instance']
            except KeyError:
                pass

            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'message': message
            }))
            
        except Exception as e:
            logger.error(f"Erro ao processar time_refresh_message no TimeRefreshConsumer: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': str(e)
            }))

class SyncRefreshConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        from cmj.painelset.cronometro_manager import CronometroManager
        from sapl.api.permissions import portalcmj_rpp

        super().__init__(*args, **kwargs)

        self.portalcmj_rpp = portalcmj_rpp
        self.cronometro_manager = CronometroManager()

    async def connect(self):
        #print('Conectando ao SyncConsumer')
        self.room_name = 'sync_refresh_channel'
        self.room_group_name = 'group_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as e:
            logger.error(f"Erro ao desconectar do SyncRefreshConsumer: {e}")

    # Receive message from WebSocket
    async def receive(self, text_data):
        jdata = json.loads(text_data)

        try:

            type_msg = jdata.get('type', '')

            if type_msg == 'ping':
                timestamp = jdata.get('timestamp_client', '')
                ping_now = jdata.get('ping_now', '')
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': {
                        'timestamp_server': time.time(), # timezone.now().timestamp(),
                        'timestamp_client': timestamp,
                        'ping_now': ping_now
                    }
                }))
                return

            if type_msg == 'command':
                command = jdata.get('command', '')
                app = jdata.get('app', '')
                model = jdata.get('model', '')
                params = jdata.get('params', {})
                user = self.scope.get('user')

                if app == 'painelset' and model == 'cronometro':

                    if not command:
                        await self.send(text_data=json.dumps({
                            'type': 'command_result',
                            'command': command,
                            'error': 'Comando não especificado'
                        }))
                        return

                    if not user.has_perm('painelset.change_cronometro'):
                        await self.send(text_data=json.dumps({
                            'type': 'command_result',
                            'command': command,
                            'error': 'Usuário não autenticado'
                        }))
                        return

                    if command in ['start', 'pause', 'resume', 'stop', 'add_time']:
                        cronometro_id = params.get('id')
                        seconds = params.get('seconds', 0)
                        if not cronometro_id:
                            await self.send(text_data=json.dumps({
                                'type': 'command_result',
                                'command': command,
                                'error': 'ID do cronômetro não especificado'
                            }))
                            return

                        command_manager = getattr(self.cronometro_manager, f'{command}_cronometro', None)
                        if not command_manager:
                            await self.send(text_data=json.dumps({
                                'type': 'command_result',
                                'command': command,
                                'error': f'Comando inválido: {command}'
                            }))
                            return

                        result = await database_sync_to_async(
                            command_manager
                        )(cronometro_id, seconds=seconds if command == 'add_time' else None)

                        #await self.send(text_data=json.dumps({
                        #    'type': 'command_result',
                        #    'command': command,
                        #    'result': result
                        #}))
        except Exception as e:
            logger.error(f"Erro ao processar mensagem no SyncRefreshConsumer: {e}")
            await self.send(text_data=json.dumps({
                'type': 'command_result',
                'command': jdata.get('command', ''),
                'error': str(e)
            }))


    async def command_result(self, event):
        """Enviar resultado do comando para o cliente"""
        await self.send(text_data=json.dumps({
            'type': 'command_result',
            'command': event['command'],
            'result': event['result']
        }))

    # Receive message from room group
    async def sync_refresh_message(self, event):

        try:

            message = event['message']
            app = message.get('app')
            model = message.get('model')

            u = self.scope.get('user')

            key = f"{app}:{model}"
            perms_publicas = self.portalcmj_rpp.get(key, set())

            perm_detail = f"{app}.detail_{model}"
            perm_view = f"{app}.view_{model}"

            if u.is_anonymous and not perms_publicas:
                detail_perm = False
            elif u.is_anonymous:
                detail_perm = perm_detail in perms_publicas or perm_view in perms_publicas
            elif not u.is_superuser:
                detail_perm = u.has_perm(perm_detail) or u.has_perm(perm_view)
            else:
                detail_perm = True

            try:
                if not detail_perm:
                    del message['instance']
            except KeyError:
                pass

            # Send message to WebSocket
            await self.send(text_data=json.dumps(event))

        except Exception as e:
            logger.error(f"Erro ao processar sync_refresh_message no SyncRefreshConsumer: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': str(e)
            }))