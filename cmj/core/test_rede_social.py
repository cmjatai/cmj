"""O signal de rede social não publica nada durante os testes."""

from unittest import mock

import pytest
from django.utils import timezone
from model_bakery import baker

from cmj.core import tasks
from sapl.materia.models import MateriaLegislativa


@pytest.mark.django_db
def test_salvar_materia_aciona_a_task_mas_nao_envia():
    task = tasks.task_send_rede_social
    with mock.patch("cmj.core.tasks.requests.post") as post, mock.patch.object(
        task, "apply_async", wraps=task.apply_async
    ) as apply_async:
        materia = baker.make(MateriaLegislativa, data_apresentacao=timezone.localdate())

    materia.refresh_from_db()
    assert apply_async.called
    assert "telegram" in materia.metadata["send"]
    assert not post.called


@pytest.mark.django_db
def test_toda_funcao_de_envio_esta_neutralizada():
    envios = [nome for nome in vars(tasks) if nome.startswith("send_")]

    assert "send_telegram_materia_materialegislativa" in envios
    assert "send_telegram_sigad_documento" in envios
    assert all(getattr(tasks, nome)(1) is None for nome in envios)
