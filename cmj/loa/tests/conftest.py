"""Fixtures dos testes de LOA.

Perfis de usuário usados nas specs de fases da emenda (docs/specs/loa/fases-emenda.md):

- autor: operador de autor ligado a um parlamentar da LOA, sem permissões de LOA;
- editor contábil: tem só ``loa.emendaloa_full_editor``;
- Operador da LOA: tem ``add_emendaloa``, ``change_emendaloa`` e ``emendaloa_full_editor``;
- superusuário.
"""

from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from model_mommy import mommy
from rest_framework.test import APIClient

from cmj.loa.models import (
    Agrupamento,
    AgrupamentoEmendaLoa,
    EmendaLoa,
    EmendaLoaParlamentar,
    Loa,
    UnidadeOrcamentaria,
)
from sapl.base.models import Autor, OperadorAutor, TipoAutor
from sapl.parlamentares.models import Parlamentar

ANO = 2027


def _perm(codename, model="emendaloa"):
    return Permission.objects.get(
        content_type__app_label="loa",
        content_type__model=model,
        codename=codename,
    )


def _make_user(username, perms=(), is_superuser=False):
    user = get_user_model().objects.create_user(
        email=f"{username}@test.local",
        password="testpass123!",
    )
    user.is_superuser = is_superuser
    user.is_staff = is_superuser
    user.save()
    for codename, model in perms:
        user.user_permissions.add(_perm(codename, model))
    return get_user_model().objects.get(pk=user.pk)  # limpa cache de permissões


@pytest.fixture(autouse=True)
def _sem_ia():
    """Evita chamadas a LLM nos fluxos de agrupamento."""
    with mock.patch(
        "cmj.loa.models.m_agrupamento.Agrupamento.update_finalidade_com_ia",
        lambda self: None,
    ):
        yield


@pytest.fixture
def loa(db):
    return mommy.make(Loa, ano=ANO, publicado=True)


@pytest.fixture
def unidade(loa):
    return mommy.make(
        UnidadeOrcamentaria,
        loa=loa,
        codigo="01",
        especificacao="Unidade Teste",
        recebe_emenda_impositiva=True,
    )


@pytest.fixture
def parlamentar(loa):
    p = mommy.make(Parlamentar, nome_parlamentar="Parlamentar A", nome_completo="A")
    loa.parlamentares.add(p)
    return p


@pytest.fixture
def parlamentar_b(loa):
    p = mommy.make(Parlamentar, nome_parlamentar="Parlamentar B", nome_completo="B")
    loa.parlamentares.add(p)
    return p


def _make_autor(username, parlamentar):
    tipo_autor = TipoAutor.objects.filter(descricao="Parlamentar").first() or (
        mommy.make(TipoAutor, descricao="Parlamentar")
    )
    autor = mommy.make(
        Autor,
        tipo=tipo_autor,
        nome=parlamentar.nome_parlamentar,
        content_type=ContentType.objects.get_for_model(Parlamentar),
        object_id=parlamentar.id,
    )
    user = _make_user(username)
    mommy.make(OperadorAutor, user=user, autor=autor)
    return get_user_model().objects.get(pk=user.pk)


@pytest.fixture
def autor(parlamentar):
    return _make_autor("autor_a", parlamentar)


@pytest.fixture
def autor_b(parlamentar_b):
    return _make_autor("autor_b", parlamentar_b)


@pytest.fixture
def editor_contabil(db):
    return _make_user(
        "editor_contabil",
        perms=[
            ("emendaloa_full_editor", "emendaloa"),
        ],
    )


@pytest.fixture
def operador_loa(db):
    return _make_user(
        "operador_loa",
        perms=[
            ("add_emendaloa", "emendaloa"),
            ("change_emendaloa", "emendaloa"),
            ("emendaloa_full_editor", "emendaloa"),
        ],
    )


@pytest.fixture
def responsavel_coletivas(loa, operador_loa):
    """Operador da LOA definido como responsável pelas coletivas da LOA (LOA-FASE-071)."""
    loa.responsavel_coletivas = operador_loa
    loa.save()
    return operador_loa


@pytest.fixture
def superuser(db):
    return _make_user("super", is_superuser=True)


@pytest.fixture
def make_emenda(loa, unidade):
    def _make(fase=EmendaLoa.PROPOSTA, owner=None, parlamentar=None, **kwargs):
        kwargs.setdefault("finalidade", "Finalidade de teste")
        kwargs.setdefault("tipo", EmendaLoa.DIVERSOS)
        kwargs.setdefault("valor", Decimal("1000.00"))
        el = EmendaLoa(
            loa=kwargs.pop("loa", loa),
            unidade=kwargs.pop("unidade", unidade),
            fase=fase,
            owner=owner,
            **kwargs,
        )
        el.save()
        if parlamentar:
            EmendaLoaParlamentar.objects.create(
                emendaloa=el, parlamentar=parlamentar, valor=el.valor
            )
        return EmendaLoa.all_objects.all_objects().get(pk=el.pk)

    return _make


@pytest.fixture
def agrupamento(loa):
    return mommy.make(Agrupamento, loa=loa, nome="Agrupamento", finalidade="Global")


@pytest.fixture
def api():
    def _client(user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    return _client


def recarregar(emenda):
    return EmendaLoa.all_objects.all_objects().get(pk=emenda.pk)


__all__ = ["recarregar", "AgrupamentoEmendaLoa"]
