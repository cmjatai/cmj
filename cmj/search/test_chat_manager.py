from types import SimpleNamespace
from unittest import mock

import pytest

from cmj.core.models import User
from cmj.search.chat_manager import ChatManager
from cmj.search.models import ChatMessage, ChatSession
from cmj.utils.genia import IAGenaiBase


@pytest.fixture
def manager():
    with mock.patch("cmj.search.chat_manager.IAGenaiBase") as ia_cls:
        ia_cls.return_value.ia_model_name = "modelo-teste"
        yield ChatManager()


@pytest.fixture
def users(db):
    return (
        User.objects.create(email="dono@example.com"),
        User.objects.create(email="outro@example.com"),
    )


def _fake_response(text="resposta"):
    response = mock.Mock()
    response.text = text
    response.usage_metadata = SimpleNamespace(total_token_count=10)
    return response


@pytest.mark.django_db
def test_sessao_de_outro_usuario_e_recusada(manager, users):
    dono, outro = users
    manager.add_message_to_context("sess_1", "user", "pergunta", dono)

    with pytest.raises(PermissionError):
        manager.add_message_to_context("sess_1", "user", "invasao", outro)

    assert ChatMessage.objects.filter(chat__session_id="sess_1").count() == 1
    assert manager.get_context_for_gemini("sess_1", user=outro) == []


@pytest.mark.django_db
def test_falha_da_ia_remove_pergunta_do_historico(manager, users):
    dono, _ = users
    manager.ia.chat_send_message.side_effect = RuntimeError("falha")

    with pytest.raises(RuntimeError):
        manager.process_user_message("sess_2", "pergunta", dono)

    assert ChatMessage.objects.filter(chat__session_id="sess_2").count() == 0
    assert ChatSession.objects.filter(session_id="sess_2").exists()


@pytest.mark.django_db
def test_resposta_do_modelo_e_salva_com_metadata(manager, users):
    dono, _ = users
    manager.ia.chat_send_message.return_value = _fake_response("ok")

    msg = manager.process_user_message("sess_3", "pergunta", dono)

    assert msg.role == "model"
    assert msg.content == "ok"
    assert msg.metadata["ia_model_name"] == "modelo-teste"
    assert msg.metadata["rag_results"]["rag_query"] == []
    assert msg.metadata["rag_results"]["rag_infos"]["total_token_count"] == 10


@pytest.mark.django_db
def test_chat_e_criado_a_cada_mensagem_e_cota_registrada(db):
    quota = mock.Mock()
    with mock.patch("cmj.utils.genia.genai.Client") as client_cls:
        client = client_cls.return_value
        ia = IAGenaiBase()
        with mock.patch.object(
            IAGenaiBase, "retrieve_quota_if_available", return_value=quota
        ):
            ia.chat_send_message("a", [], tools=[lambda query: query])
            ia.chat_send_message("b", [], tools=[lambda query: query])

    assert client.chats.create.call_count == 2
    assert quota.create_log.call_count == 2
