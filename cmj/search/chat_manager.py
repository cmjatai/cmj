
import json
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta

from cmj.search.models import ChatMessage, ChatSession

class ChatContextManager:
    def __init__(self):
        self.CONTEXT_TTL = 3600  # 1 hora de inatividade

    def get_session_key(self, session_id):
        return f"chat_context:{session_id}"

    def get_history_key(self, session_id):
        return f"chat_history:{session_id}"

    # Salvar novo mensagem no contexto ATIVO
    def add_message_to_context(self, session_id, role, content):
        """
        Adiciona mensagem ao Cache (conversa ativa)
        """
        history_key = self.get_history_key(session_id)

        message = {
            "role": role,
            "parts": [{"text": content}]  # Formato esperado pela SDK Gemini
        }

        # Recupera lista atual ou inicia nova
        history = cache.get(history_key, [])
        history.append(message)

        # Salva no cache com TTL renovado
        cache.set(history_key, history, self.CONTEXT_TTL)

    # Recuperar contexto COMPLETO para o Gemini
    def get_context_for_gemini(self, session_id):
        """
        Retorna o histórico completo no formato que Gemini espera
        """
        history_key = self.get_history_key(session_id)
        return cache.get(history_key, [])

    # Limpar contexto (usuário abandona conversa)
    def clear_session_context(self, session_id):
        """
        Deleta do Cache quando usuário sai
        """
        history_key = self.get_history_key(session_id)
        cache.delete(history_key)

    # Exportar para banco de dados ANTES de limpar
    def export_to_database(self, session_id, user):
        """
        Salva todo o contexto do Cache no banco permanente
        """
        history_key = self.get_history_key(session_id)
        history = cache.get(history_key, [])

        if not history:
            return None

        # Cria ou obtém a sessão
        chat_session, _ = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={'user': user}
        )

        # Verifica quantas mensagens já existem para evitar duplicatas
        existing_count = chat_session.messages.count()

        # Se o cache tem mais mensagens que o banco, salva as novas
        if len(history) > existing_count:
            new_messages_data = history[existing_count:]

            messages = []
            for msg in new_messages_data:
                messages.append(
                    ChatMessage(
                        chat=chat_session,
                        role=msg['role'],
                        content=msg['parts'][0]['text']
                    )
                )

            ChatMessage.objects.bulk_create(messages, batch_size=100)

            # Atualiza o título se ainda for o padrão e houver mensagem do usuário
            if chat_session.title == "Nova Conversa":
                for msg in history:
                    if msg['role'] == 'user':
                        # Limita o título a 100 caracteres
                        content = msg['parts'][0]['text']
                        new_title = content[:100]
                        if len(content) > 100:
                            new_title += "..."
                        chat_session.title = new_title
                        chat_session.save()
                        break

        return chat_session

    # Restaurar contexto anterior
    def load_session_context(self, session_id):
        """
        Carrega histórico do banco para o Cache (reanimar sessão anterior)
        """
        try:
            chat_session = ChatSession.objects.get(session_id=session_id)
            messages = chat_session.messages.all().order_by('timestamp')

            history_key = self.get_history_key(session_id)

            history = []
            for msg in messages:
                message_data = {
                    "role": msg.role,
                    "parts": [{"text": msg.content}]
                }
                history.append(message_data)

            cache.set(history_key, history, self.CONTEXT_TTL)
            return len(messages)
        except ChatSession.DoesNotExist:
            return 0