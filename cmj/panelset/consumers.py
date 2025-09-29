
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Timer
from .timer_manager import TimerManager

class TimerConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer para atualizações em tempo real dos cronômetros
    Integra com o sistema de padrões de design
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timer_id = None
        self.timer_group_name = None
        self.timer_manager = TimerManager()

    async def connect(self):
        # Pegar ID do cronômetro da URL
        self.timer_id = self.scope['url_route']['kwargs']['timer_id']
        self.timer_group_name = f'timer_{self.timer_id}'

        # Juntar-se ao grupo do cronômetro
        await self.channel_layer.group_add(
            self.timer_group_name,
            self.channel_name
        )

        await self.accept()

        # Enviar estado inicial do cronômetro
        timer_data = await self.get_timer_data(self.timer_id)
        if timer_data:
            await self.send(text_data=json.dumps({
                'type': 'timer_state',
                'timer': timer_data
            }))

    async def disconnect(self, close_code):
        # Sair do grupo do cronômetro
        if self.timer_group_name:
            await self.channel_layer.group_discard(
                self.timer_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Recebe comandos do cliente via WebSocket"""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            timer_id = data.get('timer_id', self.timer_id)

            result = None

            # Executar comandos via TimerManager (Mediator Pattern)
            if command == 'start':
                result = await database_sync_to_async(
                    self.timer_manager.start_timer
                )(timer_id)

            elif command == 'pause':
                result = await database_sync_to_async(
                    self.timer_manager.pause_timer
                )(timer_id)

            elif command == 'resume':
                result = await database_sync_to_async(
                    self.timer_manager.resume_timer
                )(timer_id)

            elif command == 'stop':
                result = await database_sync_to_async(
                    self.timer_manager.stop_timer
                )(timer_id)

            elif command == 'get_tree':
                tree_data = await database_sync_to_async(
                    self.timer_manager.get_timer_tree
                )(timer_id)
                result = {'success': True, 'tree': tree_data}

            # Enviar resultado de volta
            if result:
                await self.send(text_data=json.dumps({
                    'type': 'command_result',
                    'command': command,
                    'result': result
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
    async def timer_update(self, event):
        """Atualização de estado do cronômetro"""
        await self.send(text_data=json.dumps({
            'type': 'timer_update',
            'timer_id': event['timer_id'],
            'state': event['state'],
            'elapsed_time': event['elapsed_time'],
            'remaining_time': event['remaining_time']
        }))

    async def child_timer_update(self, event):
        """Atualização de cronômetro filho"""
        await self.send(text_data=json.dumps({
            'type': 'child_update',
            'child_timer_id': event['child_timer_id'],
            'parent_timer_id': event['parent_timer_id'],
            'state': event['state']
        }))

    @database_sync_to_async
    def get_timer_data(self, timer_id):
        """Busca dados do cronômetro de forma assíncrona"""
        try:
            timer = Timer.objects.get(id=timer_id)
            return {
                'id': str(timer.id),
                'name': timer.name,
                'state': timer.state,
                'duration': timer.duration.total_seconds(),
                'elapsed_time': timer.elapsed_time.total_seconds(),
                'remaining_time': timer.remaining_time.total_seconds(),
                'parent_id': str(timer.parent.id) if timer.parent else None,
                'children_count': timer.children.count(),
                'stop_parent_on_finish': timer.stop_parent_on_finish,
                'reduce_parent_time': timer.reduce_parent_time
            }
        except Timer.DoesNotExist:
            return None