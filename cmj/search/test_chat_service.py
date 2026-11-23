"""Quem consulta as sessões e as mensagens do chat (docs/specs/api/acesso.md)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from model_bakery import baker

from cmj.search.models import ChatMessage, ChatSession
from cmj.search.services.s_chat import ChatHistoricoService


@pytest.fixture
def conversas(django_user_model):
    """Dois usuários, cada um com uma sessão de duas mensagens."""
    feitas = {}
    for nome in ("ana", "bia"):
        user = django_user_model.objects.create_user(
            email=f"{nome}@exemplo.invalid", password="senha-de-teste-123"
        )
        sessao = baker.make(ChatSession, user=user, session_id=f"sessao-{nome}")
        mensagens = baker.make(ChatMessage, chat=sessao, role="user", _quantity=2)
        feitas[nome] = (user, sessao, mensagens)
    return feitas


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-036")
def test_usuario_consulta_so_as_proprias_sessoes_e_mensagens(conversas):
    ana, sessao_da_ana, mensagens_da_ana = conversas["ana"]

    sessoes = ChatHistoricoService.sessoes_do_usuario(ana, ChatSession.objects.all())
    mensagens = ChatHistoricoService.mensagens_do_usuario(
        ana, ChatMessage.objects.all()
    )

    assert list(sessoes) == [sessao_da_ana]
    assert set(mensagens) == set(mensagens_da_ana)


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-036")
@pytest.mark.parametrize("user", [None, AnonymousUser()])
def test_sem_usuario_autenticado_nada_do_chat_e_consultado(conversas, user):
    assert not ChatHistoricoService.sessoes_do_usuario(
        user, ChatSession.objects.all()
    ).exists()
    assert not ChatHistoricoService.mensagens_do_usuario(
        user, ChatMessage.objects.all()
    ).exists()


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-036")
def test_so_o_dono_grava_mensagem_na_sessao(conversas):
    ana, sessao_da_ana, _ = conversas["ana"]
    bia, _, _ = conversas["bia"]

    assert ChatHistoricoService.e_dono_da_sessao(ana, sessao_da_ana)
    assert not ChatHistoricoService.e_dono_da_sessao(bia, sessao_da_ana)
    assert not ChatHistoricoService.e_dono_da_sessao(AnonymousUser(), sessao_da_ana)
