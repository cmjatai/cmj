"""O que o registro de auditoria guarda (docs/specs/api/acesso.md)."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import RequestFactory

from cmj.core.models import AuditLog
from cmj.core.services.s_auditoria import AuditoriaService

pytestmark = [pytest.mark.django_db, pytest.mark.spec("API-ACS-042")]


def _registro(model_name, fields):
    return AuditLog.objects.create(
        operation="U",
        app_name="core",
        model_name=model_name,
        obj_id=1,
        obj=[{"model": f"core.{model_name}", "pk": 1, "fields": fields}],
    )


def test_registro_de_usuario_nao_guarda_o_campo_password(django_user_model):
    operador = django_user_model.objects.create_superuser(
        email="operador@exemplo.invalid", password="senha-de-teste-123"
    )
    usuario = django_user_model.objects.create_user(
        email="usuario@exemplo.invalid", password="senha-de-teste-123"
    )

    # a auditoria identifica quem alterou pela requisição em curso
    request = RequestFactory().get("/")
    request.user = operador
    usuario.first_name = "Nome alterado"
    usuario.save()

    registro = AuditLog.objects.filter(
        app_name="core", model_name="user", obj_id=usuario.pk
    ).first()
    campos = registro.obj[0]["fields"]
    assert registro.user == operador
    assert "password" not in campos
    assert campos["first_name"] == "Nome alterado"
    assert campos["email"] == "usuario@exemplo.invalid"


def test_servico_retira_so_os_campos_nao_guardados():
    obj = [{"pk": 1, "fields": {"email": "a@exemplo.invalid", "password": "valor"}}]

    assert AuditoriaService.sem_campos_nao_guardados(obj) == [
        {"pk": 1, "fields": {"email": "a@exemplo.invalid"}}
    ]
    assert AuditoriaService.sem_campos_nao_guardados({"q": "busca"}) == {"q": "busca"}
    assert AuditoriaService.sem_campos_nao_guardados(None) is None


def test_command_limpa_os_registros_ja_gravados():
    antigo = _registro("user", {"email": "a@exemplo.invalid", "password": "valor"})
    outro = _registro("areatrabalho", {"nome": "Área"})
    saida = StringIO()

    call_command("auditlog_limpa_credenciais", stdout=saida)

    antigo.refresh_from_db()
    outro.refresh_from_db()
    assert antigo.obj[0]["fields"] == {"email": "a@exemplo.invalid"}
    assert outro.obj[0]["fields"] == {"nome": "Área"}
    assert "1 registros alterados" in saida.getvalue()


def test_command_com_dry_run_so_conta():
    antigo = _registro("user", {"email": "a@exemplo.invalid", "password": "valor"})
    saida = StringIO()

    call_command("auditlog_limpa_credenciais", "--dry-run", stdout=saida)

    antigo.refresh_from_db()
    assert "password" in antigo.obj[0]["fields"]
    assert "1 registros seriam alterados" in saida.getvalue()
