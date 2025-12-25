import logging
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from google import genai
from django.conf import settings

from cmj.search.models import Embedding
from .chat_manager import ChatContextManager
from cmj.genia import IAGenaiBase

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.session_id = None
        self.context_manager = ChatContextManager()
        self.ia = None

    async def connect(self):
        self.user = self.scope['user']
        self.session_id = self.scope['url_route']['kwargs']['session_id']

        if self.user == AnonymousUser() or not self.user.has_perm('search.can_use_chat_module'):
            await self.close()
            return

        # Configure Gemini
        self.ia = await sync_to_async(IAGenaiBase)()
        self.ia.response_mime_type = 'text/plain'
        self.ia.ia_model_name = 'gemini-3-flash-preview'

        # Carrega histórico anterior do banco (se existir)
        await self.load_previous_context()

        # Recupera histórico formatado para o frontend
        history = await self.get_formatted_history()

        await self.channel_layer.group_add(
            f"chat_{self.session_id}",
            self.channel_name
        )
        await self.accept()

        await self.send(json.dumps({
            "type": "connection_established",
            "session_id": self.session_id,
            "history": history
        }))

    async def disconnect(self, close_code):
        # CRÍTICO: Salvar contexto ao desconectar
        await self.save_context_to_database()

        await self.channel_layer.group_discard(
            f"chat_{self.session_id}",
            self.channel_name
        )

    @sync_to_async
    def load_previous_context(self):
        """Carrega histórico do banco para Cache"""
        return self.context_manager.load_session_context(self.session_id)

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
            user_message = data.get('message', '')

            # Salva mensagem do usuário no contexto
            self.context_manager.add_message_to_context(
                self.session_id, 'user', user_message
            )

            # Obtém histórico completo do Cache
            history = self.context_manager.get_context_for_gemini(self.session_id)

            # Envia para Gemini com histórico
            response = await self.query_gemini(history)

            # Salva resposta do modelo no contexto
            self.context_manager.add_message_to_context(
                self.session_id, 'model', response
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

            # Sincroniza com o banco de dados após a interação
            await self.save_context_to_database()

        except Exception as e:
            await self.send_error(str(e))

    async def query_gemini(self, history):
        """Envia para Gemini com histórico completo"""

        def buscar_na_base_dados(query: str) -> str:
            """Busca informações específicas na base de dados interna ."""
            logger.info(f"[Sistema] LLM solicitou busca por: {query}")

            ia_embedding = IAGenaiBase()
            query_embedding = ia_embedding.embed_content(query)
            context = Embedding.make_context(query_embedding)

            return context

        def sync_call():
            response = self.ia.generate_content(
                contents=history, tools=[buscar_na_base_dados]
            )
            return response.text

        return await sync_to_async(sync_call)()

    @sync_to_async
    def save_context_to_database(self):
        """Persiste contexto ao desconectar"""
        return self.context_manager.export_to_database(self.session_id, self.user)

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