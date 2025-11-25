import asyncio
import time
import json
import logging


from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.utils import timezone

logger = logging.getLogger(__name__)

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
                ping_now = jdata.get('ping_now', '')
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': {
                        'timestamp_server': time.time() * 1000,
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

                    has_perm = await database_sync_to_async(
                        user.has_perm
                    )('painelset.change_cronometro')
                    if not has_perm:
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
            #logger.info('passou sync_refresh_message')
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
                detail_perm1 = await database_sync_to_async(u.has_perm)(perm_detail)
                detail_perm2 = await database_sync_to_async(u.has_perm)(perm_view)
                detail_perm = detail_perm1 or detail_perm2
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


class CronometroConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer para atualizações em tempo real dos cronômetros
    Integra com o sistema de padrões de design
    """

    def __init__(self, *args, **kwargs):
        from cmj.painelset.cronometro_manager import CronometroManager

        super().__init__(*args, **kwargs)
        self.cronometro_id = None
        self.cronometro_group_name = None

        self.cronometro_manager = CronometroManager()

    # async def estou_vivo(self):
    #     while True:
    #         print(f'Estou vivo {self.cronometro_group_name} {timezone.now()}')
    #         await asyncio.sleep(5)  # Envia a cada 5 segundos

    async def connect(self):
        # Pegar ID do cronômetro da URL
        self.cronometro_id = self.scope['url_route']['kwargs']['cronometro_id']
        self.cronometro_group_name = f'cronometro_{self.cronometro_id}'
        print(self.scope['user'], timezone.now(), self.cronometro_group_name)

        # Juntar-se ao grupo do cronômetro
        await self.channel_layer.group_add(
            self.cronometro_group_name,
            self.channel_name
        )

        await self.accept()
        # asyncio.create_task(self.estou_vivo())

        # Enviar estado inicial do cronômetro

        cronometro_data = await database_sync_to_async(
            self.cronometro_manager.get_cronometro_data
        )(self.cronometro_id)
        if cronometro_data:
            await self.send(text_data=json.dumps({
                'type': 'command_result',
                'command': 'get',
                'result': cronometro_data
            }))

    async def disconnect(self, close_code):
        # Sair do grupo do cronômetro
        if self.cronometro_group_name:
            await self.channel_layer.group_discard(
                self.cronometro_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Recebe comandos do cliente via WebSocket"""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            cronometro_id = data.get('cronometro_id', self.cronometro_id)

            result = None

            # Executar comandos via CronometroManager (Mediator Pattern)
            if command == 'start':
                result = await database_sync_to_async(
                    self.cronometro_manager.start_cronometro
                )(cronometro_id)

            elif command == 'pause':
                result = await database_sync_to_async(
                    self.cronometro_manager.pause_cronometro
                )(cronometro_id)

            elif command == 'resume':
                result = await database_sync_to_async(
                    self.cronometro_manager.resume_cronometro
                )(cronometro_id)

            elif command == 'stop':
                result = await database_sync_to_async(
                    self.cronometro_manager.stop_cronometro
                )(cronometro_id)

            elif command == 'get':
                result = await database_sync_to_async(
                    self.cronometro_manager.get_cronometro_data
                )(cronometro_id)

            elif command == 'add_time':
                seconds = data.get('seconds', 0)
                result = await database_sync_to_async(
                    self.cronometro_manager.add_time
                )(cronometro_id, seconds)

            # Enviar resultado de volta
            if result:
                """await self.send(text_data=json.dumps({
                    'type': 'command_result',
                    'command': command,
                    'result': result
                }))"""
                await self.channel_layer.group_send(
                    self.cronometro_group_name, {
                        'type': 'command_result',
                        'command': command,
                        'result': result
                    }
                )

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def command_result(self, event):
        """Enviar resultado do comando para o cliente"""
        await self.send(text_data=json.dumps({
            'type': 'command_result',
            'command': event['command'],
            'result': event['result']
        }))

    # Handlers para mensagens do grupo (enviadas pela Chain of Responsibility)
    async def cronometro_update(self, event):
        """Atualização de estado do cronômetro"""
        await self.send(text_data=json.dumps({
            'type': 'cronometro_update',
            'cronometro_id': event['cronometro_id'],
            'state': event['state'],
            'elapsed_time': event['elapsed_time'],
            'remaining_time': event['remaining_time']
        }))

    async def child_cronometro_update(self, event):
        """Atualização de cronômetro filho"""
        await self.send(text_data=json.dumps({
            'type': 'child_update',
            'child_cronometro_id': event['child_cronometro_id'],
            'parent_cronometro_id': event['parent_cronometro_id'],
            'state': event['state']
        }))
