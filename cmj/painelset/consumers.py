
import asyncio
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from cmj.api.serializers_painelset import CronometroSerializer
from .models import Cronometro
from .cronometro_manager import CronometroManager
from django.utils import timezone

class CronometroConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer para atualizações em tempo real dos cronômetros
    Integra com o sistema de padrões de design
    """

    def __init__(self, *args, **kwargs):
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
