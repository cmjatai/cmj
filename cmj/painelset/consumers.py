
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

    async def connect(self):
        # Pegar ID do cronômetro da URL
        print(self.scope['user'], timezone.now())
        self.cronometro_id = self.scope['url_route']['kwargs']['cronometro_id']
        self.cronometro_group_name = f'cronometro_{self.cronometro_id}'

        # Juntar-se ao grupo do cronômetro
        await self.channel_layer.group_add(
            self.cronometro_group_name,
            self.channel_name
        )

        await self.accept()

        # Enviar estado inicial do cronômetro
        cronometro_data = await self.get_cronometro_data(self.cronometro_id)
        if cronometro_data:
            await self.send(text_data=json.dumps({
                'type': 'cronometro_state',
                'cronometro': cronometro_data
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

            elif command == 'get_tree':
                tree_data = await database_sync_to_async(
                    self.cronometro_manager.get_cronometro_tree
                )(cronometro_id)
                result = {'success': True, 'tree': tree_data}

            # Enviar resultado de volta
            if result:
                await self.send(text_data=json.dumps({
                    'type': 'command_result',
                    'command': command,
                    'result': result,
                    'cronometro': await self.get_cronometro_data(cronometro_id)
                }))

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

    @database_sync_to_async
    def get_cronometro_data(self, cronometro_id):
        """Busca dados do cronômetro de forma assíncrona"""
        try:
            cronometro = Cronometro.objects.get(id=cronometro_id)
            return CronometroSerializer(cronometro).data
            return {
                'id': cronometro.id,
                'name': cronometro.name,
                'state': cronometro.state,
                'duration': cronometro.duration.total_seconds(),
                'elapsed_time': cronometro.elapsed_time.total_seconds(),
                'remaining_time': cronometro.remaining_time.total_seconds(),
                'parent_id': str(cronometro.parent.id) if cronometro.parent else None,
                'children_count': cronometro.children.count(),
                'pause_parent_on_start': cronometro.pause_parent_on_start
            }
        except Cronometro.DoesNotExist:
            return None