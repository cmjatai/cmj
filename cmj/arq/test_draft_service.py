"""Quem consulta os drafts e as mídias deles (docs/specs/api/acesso.md)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from model_bakery import baker

from cmj.arq.models import Draft, DraftMidia
from cmj.arq.services.s_draft import DraftService


@pytest.fixture
def drafts(django_user_model):
    """Dois usuários, cada um com um draft de duas mídias."""
    feitos = {}
    for nome in ("ana", "bia"):
        user = django_user_model.objects.create_user(
            email=f"{nome}@exemplo.invalid", password="senha-de-teste-123"
        )
        draft = baker.make(Draft, owner=user)
        midias = baker.make(DraftMidia, draft=draft, _quantity=2)
        feitos[nome] = (user, draft, midias)
    return feitos


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-037")
def test_usuario_consulta_so_os_proprios_drafts_e_midias(drafts):
    ana, draft_da_ana, midias_da_ana = drafts["ana"]

    assert list(DraftService.drafts_do_usuario(ana, Draft.objects.all())) == [
        draft_da_ana
    ]
    assert set(DraftService.midias_do_usuario(ana, DraftMidia.objects.all())) == set(
        midias_da_ana
    )


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-037")
@pytest.mark.parametrize("user", [None, AnonymousUser()])
def test_sem_usuario_autenticado_nenhum_draft_e_consultado(drafts, user):
    assert not DraftService.drafts_do_usuario(user, Draft.objects.all()).exists()
    assert not DraftService.midias_do_usuario(user, DraftMidia.objects.all()).exists()


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-037")
def test_so_o_dono_grava_midia_no_draft(drafts):
    ana, draft_da_ana, _ = drafts["ana"]
    bia, _, _ = drafts["bia"]

    assert DraftService.e_dono_do_draft(ana, draft_da_ana)
    assert not DraftService.e_dono_do_draft(bia, draft_da_ana)
    assert not DraftService.e_dono_do_draft(AnonymousUser(), draft_da_ana)
