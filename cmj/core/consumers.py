import json

from channels.generic.websocket import AsyncWebsocketConsumer


class TimeRefreshConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = 'time_refresh_channel'
        self.room_group_name = 'group_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'time_refresh_message',
                'message': message
            }
        )

    # Receive message from room group
    async def time_refresh_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
