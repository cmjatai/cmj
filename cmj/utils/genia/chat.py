import logging

from cmj.core.models import IAQuota
from cmj.utils.genia.base import IAGenaiBase
from cmj.utils.genia.genia_system_instruction_v3 import rag_system_instruction

logger = logging.getLogger(__name__)


class IAChatService(IAGenaiBase):
    """
    Conversa do chat RAG (cmj.search.chat_manager.ChatManager).

    Reúne o que é só do chat: a system instruction, a resposta em texto, a
    chave de cota e os limites de uso por usuário.
    Spec: docs/specs/genia/chat.md
    """

    quota_service_name = IAQuota.ServicosAutorizados.IA_CHAT_SERVICE

    response_mime_type = "text/plain"
    system_instruction = rag_system_instruction

    # Limites de uso, aplicados pelo ChatManager e pelo ChatConsumer.
    # Superusuário não é limitado.
    MAX_SESSIONS_PER_USER = 2  # conversas novas por usuário por dia
    MAX_MESSAGES_PER_SESSION = 8  # mensagens (user + model) por conversa
    MAX_LENGTH_USER_MESSAGE = 200  # caracteres por mensagem do usuário

    def chat_send_message(self, message, history, tools=None):
        # O banco é a fonte do histórico: um Chat novo por mensagem mantém as
        # tools (e o que elas coletam) sempre associadas à mensagem corrente.
        quota = self.retrieve_quota_if_available()
        chat = self.client.chats.create(
            model=self.ia_model_name,
            config=self.build_generation_config(tools=tools),
            history=history,
        )

        response = chat.send_message(str(message))
        quota.create_log()

        return response
