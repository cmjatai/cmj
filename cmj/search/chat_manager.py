
import logging
from cmj.search.models import ChatMessage, ChatSession, Embedding
from cmj.genia import IAGenaiBase

logger = logging.getLogger(__name__)

class ChatManager:

    MAX_SESSIONS_PER_USER = 2
    MAX_MESSAGES_PER_SESSION = 8
    MAX_LENGTH_USER_MESSAGE = 200

    def __init__(self):
        self.ia = IAGenaiBase()
        self.ia.response_mime_type = 'text/plain'
        #self.ia.ia_model_name = 'gemini-3-flash-preview'

    def query_gemini(self, history):
        """Envia para Gemini com histórico completo"""

        rag_results = []

        def buscar_na_base_dados(query: str) -> str:
            """Busca informações específicas na base de dados interna ."""
            logger.info(f"[Sistema] LLM solicitou busca por: {query}")

            ia_embedding = IAGenaiBase()
            query_embedding = ia_embedding.embed_content(query)
            context = Embedding.make_context(query_embedding)

            rag_results.append({
                'query': query,
                'results': context
            })

            return context

        def sync_call():
            response = self.ia.generate_content(
                contents=history, tools=[buscar_na_base_dados]
            )
            return response.text

        #return f'RESPOSTA: len_history {len(history)}'
        return sync_call(), rag_results

    def process_user_message(self, session_id, user_message, user):
        """
        Processa a mensagem do usuário: salva, consulta a IA e salva a resposta.
        """
        # Salva mensagem do usuário no contexto
        self.add_message_to_context(session_id, 'user', user_message, user)

        # Obtém histórico completo do DB
        history = self.get_context_for_gemini(session_id)

        # Envia para Gemini com histórico
        response, rag_results = self.query_gemini(history)

        # Salva resposta do modelo no contexto
        self.add_message_to_context(session_id, 'model', response, user, metadata={'rag_results': rag_results})

        return response

    def add_message_to_context(self, session_id, role, content, user, metadata=None):
        """
        Adiciona mensagem diretamente ao banco de dados
        """
        if metadata is None:
            metadata = {}
        else:
            metadata.update({
                'ia_model_name': self.ia.ia_model_name,
            })

        # Verifica limite de sessões antes de criar uma nova
        if not ChatSession.objects.filter(session_id=session_id).exists():
            if not user.is_superuser and ChatSession.objects.filter(user=user).count() >= self.MAX_SESSIONS_PER_USER:
                raise ValueError(f"Devido aos custos com I.A. o limite de conversas por usuário atingido ({self.MAX_SESSIONS_PER_USER}).")

        # Cria ou obtém a sessão
        chat_session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={'user': user}
        )

        # Verifica limite de mensagens
        if not user.is_superuser and chat_session.messages.count() >= self.MAX_MESSAGES_PER_SESSION:
             raise ValueError(f"Devido aos custos com I.A. o limite de mensagens por conversa foi atingido ({self.MAX_MESSAGES_PER_SESSION}).")

        # Cria a mensagem
        ChatMessage.objects.create(
            chat=chat_session,
            role=role,
            content=content,
            metadata=metadata
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
