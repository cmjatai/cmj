"""Visibilidade dos textos articulados e do que pertence a eles
(docs/specs/api/acesso.md)."""

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.utils import timezone
from model_bakery import baker

from sapl.compilacao.models import (
    NINST,
    NPRIV,
    NPUBL,
    STATUS_TA_EDITION,
    STATUS_TA_IMMUTABLE_PUBLIC,
    STATUS_TA_IMMUTABLE_RESTRICT,
    STATUS_TA_PRIVATE,
    STATUS_TA_PUBLIC,
    Dispositivo,
    Nota,
    Publicacao,
    TextoArticulado,
    Vide,
)
from sapl.compilacao.services.s_visibilidade import VisibilidadeCompilacaoService

servico = VisibilidadeCompilacaoService()

PUBLICO = STATUS_TA_PUBLIC
IMUTAVEL_PUBLICO = STATUS_TA_IMMUTABLE_PUBLIC
RESTRITO = STATUS_TA_IMMUTABLE_RESTRICT
EM_EDICAO = STATUS_TA_EDITION
PRIVADO = STATUS_TA_PRIVATE


def _usuario(django_user_model, nome, permissao=None, **kwargs):
    user = django_user_model.objects.create_user(
        email=f"{nome}@exemplo.invalid", password="senha-de-teste-123", **kwargs
    )
    if permissao:
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="compilacao", codename=permissao
            )
        )
    return django_user_model.objects.get(pk=user.pk)  # limpa o cache de permissões


@pytest.fixture
def usuarios(django_user_model):
    return {
        "anonimo": AnonymousUser(),
        "comum": _usuario(django_user_model, "comum"),
        "ve_restrito": _usuario(
            django_user_model, "ve_restrito", "view_restricted_textoarticulado"
        ),
        "edita": _usuario(
            django_user_model, "edita", "change_dispositivo_edicao_dinamica"
        ),
        "dono": _usuario(django_user_model, "dono"),
        "superusuario": django_user_model.objects.create_superuser(
            email="superusuario@exemplo.invalid", password="senha-de-teste-123"
        ),
    }


@pytest.fixture
def textos(usuarios):
    """Um texto de cada estado; ``dono`` é dono de todos os que não são públicos."""
    feitos = {}
    for estado in (PUBLICO, IMUTAVEL_PUBLICO, RESTRITO, EM_EDICAO, PRIVADO):
        feitos[estado] = baker.make(TextoArticulado, privacidade=estado)
        if estado not in (PUBLICO, IMUTAVEL_PUBLICO):
            feitos[estado].owners.add(usuarios["dono"])
    return feitos


VISIVEIS_POR_USUARIO = {
    "anonimo": {PUBLICO, IMUTAVEL_PUBLICO},
    "comum": {PUBLICO, IMUTAVEL_PUBLICO},
    "ve_restrito": {PUBLICO, IMUTAVEL_PUBLICO, RESTRITO},
    "edita": {PUBLICO, IMUTAVEL_PUBLICO, EM_EDICAO},
    "dono": {PUBLICO, IMUTAVEL_PUBLICO, RESTRITO, EM_EDICAO, PRIVADO},
    # o texto privado só sai para o dono, nem para o superusuário
    "superusuario": {PUBLICO, IMUTAVEL_PUBLICO, RESTRITO, EM_EDICAO},
}


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-034")
@pytest.mark.parametrize("quem", VISIVEIS_POR_USUARIO)
def test_texto_articulado_visivel_conforme_estado_dono_e_permissao(
    quem, usuarios, textos
):
    visiveis = servico.textos_visiveis(usuarios[quem], TextoArticulado.objects.all())

    assert {t.privacidade for t in visiveis} == VISIVEIS_POR_USUARIO[quem]
    assert visiveis.count() == len(VISIVEIS_POR_USUARIO[quem])


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-034")
@pytest.mark.parametrize("quem", ["anonimo", "edita", "dono"])
def test_dispositivo_publicacao_e_vide_seguem_o_texto(quem, usuarios, textos):
    for texto in textos.values():
        dispositivo = baker.make(Dispositivo, ta=texto, ta_publicado=None)
        baker.make(Publicacao, ta=texto)
        baker.make(Vide, dispositivo_base=dispositivo, dispositivo_ref=dispositivo)
    user = usuarios[quem]
    esperado = VISIVEIS_POR_USUARIO[quem]

    dispositivos = servico.dispositivos_visiveis(user, Dispositivo.objects.all())
    publicacoes = servico.publicacoes_visiveis(user, Publicacao.objects.all())
    vides = servico.vides_visiveis(user, Vide.objects.all())

    assert {d.ta.privacidade for d in dispositivos} == esperado
    assert {p.ta.privacidade for p in publicacoes} == esperado
    assert {v.dispositivo_base.ta.privacidade for v in vides} == esperado


@pytest.fixture
def notas(usuarios, textos):
    """Uma nota de cada publicidade, todas do ``dono``, no texto público e no
    texto em edição."""
    agora = timezone.now()
    feitas = []
    for estado in (PUBLICO, EM_EDICAO):
        dispositivo = baker.make(Dispositivo, ta=textos[estado], ta_publicado=None)
        for publicidade in (NPUBL, NINST, NPRIV):
            feitas.append(
                baker.make(
                    Nota,
                    dispositivo=dispositivo,
                    publicidade=publicidade,
                    owner=usuarios["dono"],
                    publicacao=agora,
                    efetividade=agora,
                )
            )
    return feitas


NOTAS_POR_USUARIO = {
    "anonimo": {(PUBLICO, NPUBL)},
    "comum": {(PUBLICO, NPUBL), (PUBLICO, NINST)},
    "edita": {
        (PUBLICO, NPUBL),
        (PUBLICO, NINST),
        (EM_EDICAO, NPUBL),
        (EM_EDICAO, NINST),
    },
    "dono": {
        (PUBLICO, NPUBL),
        (PUBLICO, NINST),
        (PUBLICO, NPRIV),
        (EM_EDICAO, NPUBL),
        (EM_EDICAO, NINST),
        (EM_EDICAO, NPRIV),
    },
    "superusuario": {
        (PUBLICO, NPUBL),
        (PUBLICO, NINST),
        (PUBLICO, NPRIV),
        (EM_EDICAO, NPUBL),
        (EM_EDICAO, NINST),
        (EM_EDICAO, NPRIV),
    },
}


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-035")
@pytest.mark.parametrize("quem", NOTAS_POR_USUARIO)
def test_nota_visivel_conforme_publicidade_e_texto(quem, usuarios, notas):
    visiveis = servico.notas_visiveis(usuarios[quem], Nota.objects.all())

    assert {
        (n.dispositivo.ta.privacidade, n.publicidade) for n in visiveis
    } == NOTAS_POR_USUARIO[quem]
