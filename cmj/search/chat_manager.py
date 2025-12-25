
import logging
from cmj.search.models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

class ChatContextManager:

    MAX_SESSIONS_PER_USER = 2
    MAX_MESSAGES_PER_SESSION = 8

    def __init__(self):
        pass

    def add_message_to_context(self, session_id, role, content, user):
        """
        Adiciona mensagem diretamente ao banco de dados
        """
        # Verifica limite de sessões antes de criar uma nova
        if not ChatSession.objects.filter(session_id=session_id).exists():
            if ChatSession.objects.filter(user=user).count() >= self.MAX_SESSIONS_PER_USER:
                raise ValueError(f"Limite de sessões por usuário atingido ({self.MAX_SESSIONS_PER_USER}).")

        # Cria ou obtém a sessão
        chat_session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={'user': user}
        )

        # Verifica limite de mensagens
        if chat_session.messages.count() >= self.MAX_MESSAGES_PER_SESSION:
             raise ValueError(f"Limite de mensagens por sessão atingido ({self.MAX_MESSAGES_PER_SESSION}).")

        # Cria a mensagem
        ChatMessage.objects.create(
            chat=chat_session,
            role=role,
            content=content
        )

        # Atualiza timestamp da sessão
        chat_session.save()

        # Atualiza o título se ainda for o padrão e houver mensagem do usuário
        if chat_session.title == "Nova Conversa" and role == 'user':
            # Limita o título a 100 caracteres
            new_title = content[:100]
            if len(content) > 100:
                new_title += "..."
            chat_session.title = new_title
            chat_session.save()

    def get_context_for_gemini(self, session_id):
        """
        Retorna o histórico completo do banco no formato que Gemini espera
        """
        try:
            chat_session = ChatSession.objects.get(session_id=session_id)
            messages = chat_session.messages.all().order_by('timestamp')

            history = []
            for msg in messages:
                history.append({
                    "role": msg.role,
                    "parts": [{"text": msg.content}]
                })
            return history
        except ChatSession.DoesNotExist:
            return []
