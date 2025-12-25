import logging
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from google import genai
from django.conf import settings
from django.utils.html import escape

from .chat_manager import ChatManager

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.session_id = None
        self.context_manager = ChatManager()


    async def connect(self):
        self.user = self.scope['user']
        self.session_id = self.scope['url_route']['kwargs']['session_id']

        if self.user == AnonymousUser() or not self.user.has_perm('search.can_use_chat_module'):
            await self.close()
            return

        # Recupera histórico formatado para o frontend
        history = await self.get_formatted_history()

        # Controle de Concorrência: Derruba conexões anteriores na mesma sessão
        # Envia sinal para o grupo ANTES de entrar nele, para não desconectar a si mesmo
        await self.channel_layer.group_send(
            f"chat_{self.session_id}",
            {"type": "disconnect_old_connection"}
        )

        await self.channel_layer.group_add(
            f"chat_{self.session_id}",
            self.channel_name
        )
        await self.accept()

        await self.send(json.dumps({
            "type": "connection_established",
            "session_id": self.session_id,
            "history": history,
            "max_length": self.context_manager.MAX_LENGTH_USER_MESSAGE
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            f"chat_{self.session_id}",
            self.channel_name
        )

    async def disconnect_old_connection(self, event):
        """Fecha a conexão se receber sinal de nova conexão na mesma sessão"""
        await self.close(code=4001)  # 4001: Código personalizado para "Substituído por nova conexão"

    @sync_to_async
    def get_formatted_history(self):
        """Recupera histórico do cache e formata para o frontend"""
        history = self.context_manager.get_context_for_gemini(self.session_id)
        return [
            {
                "role": msg["role"],
                "content": msg["parts"][0]["text"]
            }
            for msg in history
        ]

    async def receive(self, text_data):
        if not self.user.is_authenticated or not self.user.has_perm('search.can_use_chat_module'):
            await self.send_error("Authentication required")
            await self.close()
            return

        try:
            data = json.loads(text_data)
            user_message = data.get('message', '').strip()

            if len(user_message) > self.context_manager.MAX_LENGTH_USER_MESSAGE:
                await self.send_error(f"Mensagem muito longa. O limite é de {self.context_manager.MAX_LENGTH_USER_MESSAGE} caracteres.")
                return

            user_message = escape(user_message)

            # Processa mensagem e obtém resposta
            response = await sync_to_async(self.context_manager.process_user_message)(
                self.session_id, user_message, self.user
            )

            # Envia resposta ao cliente
            await self.channel_layer.group_send(
                f"chat_{self.session_id}",
                {
                    'type': 'chat_message',
                    'message': response,
                    'role': 'model'
                }
            )

        except Exception as e:
            await self.send_error(str(e))

    async def chat_message(self, event):
        await self.send(json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'role': event['role']
        }))

    async def send_error(self, error_msg):
        await self.send(json.dumps({
            'type': 'error',
            'message': error_msg
        }))