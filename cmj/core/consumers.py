import json
import time

from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone


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
        timestamp = jdata.get('timestamp', '')

        if type_msg == 'ping' and timestamp:
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': time.time(), # timezone.now().timestamp(),
                'client_timestamp': timestamp
            }))

    # Receive message from room group
    async def time_refresh_message(self, event):

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

        if not detail_perm:
            del message['instance']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

class SyncConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        #print('Conectando ao SyncConsumer')
        self.room_name = 'sync_channel'
        self.room_group_name = 'group_%s' % self.room_name

        from sapl.api.permissions import portalcmj_rpp
        self.portalcmj_rpp = portalcmj_rpp

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        #print('Desconectando do SyncConsumer')
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        jdata = json.loads(text_data)

        type_msg = jdata.get('type', '')
        timestamp = jdata.get('timestamp', '')

        if type_msg == 'ping' and timestamp:
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp':  time.time(), #timezone.now().timestamp(),
                'client_timestamp': timestamp
            }))


    # Receive message from room group
    async def sync(self, event):

        message = event
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

        if not detail_perm:
            del message['instance']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))