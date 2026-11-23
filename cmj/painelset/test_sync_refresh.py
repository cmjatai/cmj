"""Canal de sincronização por WebSocket (docs/specs/api/acesso.md).

Os testes trocam a camada de canais por uma lista e chamam o consumer direto:
nada passa pelo Redis.
"""

import json
from types import SimpleNamespace
from unittest import mock

import pytest
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from model_bakery import baker

import sapl.api.urls  # noqa: F401  carrega os viewsets, como o URLconf faz
from cmj.painelset.consumers import SyncRefreshConsumer
from cmj.painelset.signals_sync_refresh import restringe_por_registro
from sapl.base.models import Autor
from sapl.materia.models import Proposicao, TipoMateriaLegislativa

pytestmark = [pytest.mark.django_db, pytest.mark.spec("API-ACS-047")]


def _avisos_do_canal(gravar, model):
    """Os avisos de ``model`` que o signal de sincronização manda ao canal
    enquanto ``gravar`` roda."""
    enviados = []

    async def group_send(grupo, evento):
        enviados.append(evento)

    camada = SimpleNamespace(group_send=group_send)
    with mock.patch(
        "cmj.painelset.signals_sync_refresh.get_channel_layer", return_value=camada
    ):
        gravar()
    return [e for e in enviados if e["message"]["model"] == model]


def _recebido_por(user, evento):
    """A mensagem que o consumer entrega a ``user`` para um aviso do canal."""
    entregues = []

    async def send(text_data=None, **kwargs):
        entregues.append(json.loads(text_data))

    consumer = SyncRefreshConsumer()
    consumer.scope = {"user": user}
    consumer.send = send
    async_to_sync(consumer.sync_refresh_message)(evento)
    return entregues[0]["message"]


@pytest.fixture
def com_permissao_de_detalhe(django_user_model):
    """Usuário comum com a permissão de detalhe de proposição, como a que o
    grupo de autores dá."""
    user = django_user_model.objects.create_user(
        email="operador-de-autor@exemplo.invalid", password="senha-de-teste-123"
    )
    user._perm_cache = {"materia.detail_proposicao"}
    return user


@pytest.fixture
def superusuario(django_user_model):
    return django_user_model.objects.create_superuser(
        email="superusuario@exemplo.invalid", password="senha-de-teste-123"
    )


def test_model_com_visibilidade_por_registro_vai_ao_canal_sem_o_registro(
    com_permissao_de_detalhe, superusuario
):
    autor = baker.make(Autor)

    avisos = _avisos_do_canal(
        lambda: baker.make(Proposicao, autor=autor, descricao="Rascunho do autor"),
        "proposicao",
    )

    assert avisos
    for aviso in avisos:
        assert aviso["message"]["instance"] is None
        assert "Rascunho do autor" not in json.dumps(aviso)

    for user in (com_permissao_de_detalhe, superusuario, AnonymousUser()):
        recebido = _recebido_por(user, dict(avisos[-1]))
        assert not recebido.get("instance")
        assert recebido["model"] == "proposicao"
        assert recebido["id"]


def test_model_sem_visibilidade_por_registro_continua_indo_com_o_registro():
    avisos = _avisos_do_canal(
        lambda: baker.make(TipoMateriaLegislativa, sigla="PL", descricao="Projeto"),
        "tipomaterialegislativa",
    )

    assert avisos[-1]["message"]["instance"]["descricao"] == "Projeto"

    recebido = _recebido_por(AnonymousUser(), dict(avisos[-1]))
    assert recebido["instance"]["descricao"] == "Projeto"


def test_criterio_e_o_do_viewset_do_model():
    assert restringe_por_registro(Proposicao)
    assert not restringe_por_registro(TipoMateriaLegislativa)
    # model sem rota na API não restringe
    assert not restringe_por_registro(get_user_model())
