"""
Testes para o controle de assinaturas de proposição:
  - Modelo ProposicaoAssinante (constraints, status)
  - Endpoints API:
      GET  /api/materia/proposicao/{id}/assinantes/
      POST /api/materia/proposicao/{id}/capturar_assinatura/
      POST /api/materia/proposicao/{id}/liberar_assinatura/
  - Regra de concorrência: apenas um lock ativo por proposição
  - Auto-liberação de lock expirado

Notas de infraestrutura de testes:
  - Todos os testes usam transaction=False para compatibilidade com --no-migrations
    (transaction=True causa IntegrityError no commit por FKs de auth_permission/
    content_type que ficam incompletos sem migrações reais).
  - Para IntegrityError, usa-se savepoints via transaction.atomic() interno.
  - GET assinantes/ requer usuário autenticado sem Autor (q=Q() → vê tudo),
    pois a permissão anônima só exibe proposições já incorporadas.
"""

from datetime import timedelta

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from sapl.base.models import Autor, OperadorAutor, TipoAutor
from sapl.materia.models import (
    Proposicao,
    ProposicaoAssinante,
    TipoProposicao,
)

# ===========================================================================
#  Fixtures / helpers
# ===========================================================================


@pytest.fixture
def tipo_proposicao(db):
    """TipoProposicao mínimo usando o próprio ContentType de TipoProposicao."""
    ct = ContentType.objects.get_for_model(TipoProposicao)
    return baker.make(TipoProposicao, descricao="PL Teste", content_type=ct)


@pytest.fixture
def proposicao(db, tipo_proposicao):
    """Proposicao sem data_envio (rascunho)."""
    return baker.make(
        Proposicao,
        tipo=tipo_proposicao,
        descricao="Proposição de teste",
        data_envio=None,
    )


def _criar_autor(nome="Autor A", certificado_cn=""):
    tipo = baker.make(TipoAutor, descricao=f"Tipo {nome}")
    return baker.make(Autor, tipo=tipo, nome=nome, certificado_cn=certificado_cn)


def _criar_usuario_com_autor(email, nome_autor="Parlamentar"):
    """Cria User + Autor + OperadorAutor vinculados; retorna (user, autor, token)."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user(email, password="secret123")
    autor = _criar_autor(nome=nome_autor)
    baker.make(OperadorAutor, user=user, autor=autor)
    return user, autor, user.auth_token


def _criar_usuario_sem_autor(email):
    """Cria User SEM Autor — get_queryset usa q=Q() (vê qualquer proposição)."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.create_user(email, password="secret123")
    return user, user.auth_token


def _api_client_para(token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


# ===========================================================================
#  Testes de modelo / constraints
# ===========================================================================


@pytest.mark.django_db(transaction=False)
def test_criar_assinante_pendente(proposicao):
    """Deve criar ProposicaoAssinante com status P por padrão."""
    autor = _criar_autor()
    pa = ProposicaoAssinante.objects.create(proposicao=proposicao, autor=autor)
    assert pa.status == ProposicaoAssinante.STATUS_PENDENTE
    assert pa.data_captura is None
    assert pa.data_assinatura is None


@pytest.mark.django_db(transaction=False)
def test_unique_together_proposicao_autor(proposicao):
    """Mesmo autor não pode ter dois registros para a mesma proposição."""
    autor = _criar_autor()
    ProposicaoAssinante.objects.create(proposicao=proposicao, autor=autor)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ProposicaoAssinante.objects.create(proposicao=proposicao, autor=autor)


@pytest.mark.django_db(transaction=False)
def test_unique_lock_por_proposicao(proposicao):
    """UniqueConstraint parcial: apenas um status 'A' por proposição."""
    autor_a = _criar_autor("Autor A")
    autor_b = _criar_autor("Autor B")

    ProposicaoAssinante.objects.create(
        proposicao=proposicao,
        autor=autor_a,
        status=ProposicaoAssinante.STATUS_EM_ASSINATURA,
        data_captura=timezone.now(),
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ProposicaoAssinante.objects.create(
                proposicao=proposicao,
                autor=autor_b,
                status=ProposicaoAssinante.STATUS_EM_ASSINATURA,
                data_captura=timezone.now(),
            )


@pytest.mark.django_db(transaction=False)
def test_dois_assinantes_status_s_permitido(proposicao):
    """Dois assinantes com status 'S' na mesma proposição são permitidos."""
    autor_a = _criar_autor("Autor A")
    autor_b = _criar_autor("Autor B")

    ProposicaoAssinante.objects.create(
        proposicao=proposicao,
        autor=autor_a,
        status=ProposicaoAssinante.STATUS_ASSINADO,
        data_assinatura=timezone.now(),
    )
    ProposicaoAssinante.objects.create(
        proposicao=proposicao,
        autor=autor_b,
        status=ProposicaoAssinante.STATUS_ASSINADO,
        data_assinatura=timezone.now(),
    )
    assert ProposicaoAssinante.objects.filter(proposicao=proposicao).count() == 2


# ===========================================================================
#  Testes do endpoint GET assinantes/
# ===========================================================================


@pytest.mark.django_db(transaction=False)
def test_listar_assinantes_vazio(proposicao):
    """GET assinantes/ sem nenhum assinante retorna lista vazia.

    Usa usuário sem Autor para que get_queryset use q=Q() e a proposição
    (rascunho) não seja filtrada fora do queryset.
    """
    _, token = _criar_usuario_sem_autor("staff@cmj.go.leg.br")
    client = _api_client_para(token)
    response = client.get(f"/api/materia/proposicao/{proposicao.pk}/assinantes/")
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db(transaction=False)
def test_listar_assinantes_com_dados(proposicao):
    """GET assinantes/ retorna os campos esperados para cada assinante."""
    _, token = _criar_usuario_sem_autor("staff2@cmj.go.leg.br")
    autor = _criar_autor("Vereador X")
    ProposicaoAssinante.objects.create(proposicao=proposicao, autor=autor)

    client = _api_client_para(token)
    response = client.get(f"/api/materia/proposicao/{proposicao.pk}/assinantes/")
    assert response.status_code == 200
    assert len(response.data) == 1

    item = response.data[0]
    assert item["autor_id"] == autor.pk
    assert item["status"] == ProposicaoAssinante.STATUS_PENDENTE
    assert "status_display" in item
    assert "data_captura" in item
    assert "data_assinatura" in item


@pytest.mark.django_db(transaction=False)
def test_listar_assinantes_acessivel_apos_assinar(proposicao):
    """
    Co-signatário com status S ainda pode consultar /assinantes/ para confirmar
    que sua assinatura foi processada (polling pós-upload).
    """
    _, autor_principal, _ = _criar_usuario_com_autor(
        "pa_poll@cmj.go.leg.br", "Autor Principal Poll"
    )
    _, co_sig, token = _criar_usuario_com_autor(
        "cosig_poll@cmj.go.leg.br", "Co-Sig Poll"
    )

    proposicao.autor = autor_principal
    proposicao.save(update_fields=["autor"])

    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=co_sig,
        status=ProposicaoAssinante.STATUS_ASSINADO,
        data_assinatura=timezone.now(),
    )

    client = _api_client_para(token)
    response = client.get(f"/api/materia/proposicao/{proposicao.pk}/assinantes/")
    assert response.status_code == 200
    assert any(
        item["autor_id"] == co_sig.pk
        and item["status"] == ProposicaoAssinante.STATUS_ASSINADO
        for item in response.data
    )


@pytest.mark.django_db(transaction=False)
def test_capturar_assinatura_sucesso(proposicao):
    """Assinante pendente captura lock → status vira 'A', retorna hash_code."""
    _, autor, token = _criar_usuario_com_autor("vereador@cmj.go.leg.br", "Vereador A")
    # get_queryset filtra por autor quando o user tem Autor vinculado
    proposicao.autor = autor
    proposicao.save(update_fields=["autor"])
    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=autor,
        status=ProposicaoAssinante.STATUS_PENDENTE,
    )

    client = _api_client_para(token)
    response = client.post(
        f"/api/materia/proposicao/{proposicao.pk}/capturar_assinatura/"
    )

    assert response.status_code == 200
    assert "hash_code" in response.data
    assert "data_captura" in response.data

    pa = ProposicaoAssinante.objects.get(proposicao=proposicao, autor=autor)
    assert pa.status == ProposicaoAssinante.STATUS_EM_ASSINATURA
    assert pa.data_captura is not None


@pytest.mark.django_db(transaction=False)
def test_capturar_assinatura_proposta_ja_enviada(proposicao):
    """Proposição já enviada (data_envio != None) retorna 400."""
    _, autor, token = _criar_usuario_com_autor("v2@cmj.go.leg.br", "Vereador B")
    # Vincula proposição ao autor para que get_queryset a retorne ao usuário logado
    proposicao.autor = autor
    proposicao.data_envio = timezone.now()
    proposicao.save(update_fields=["autor", "data_envio"])

    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=autor,
        status=ProposicaoAssinante.STATUS_PENDENTE,
    )

    client = _api_client_para(token)
    response = client.post(
        f"/api/materia/proposicao/{proposicao.pk}/capturar_assinatura/"
    )
    assert response.status_code == 400


@pytest.mark.django_db(transaction=False)
def test_capturar_assinatura_usuario_sem_autor(proposicao):
    """Usuário autenticado sem Autor vinculado retorna 403."""
    _, token = _criar_usuario_sem_autor("sem_autor@cmj.go.leg.br")
    client = _api_client_para(token)
    response = client.post(
        f"/api/materia/proposicao/{proposicao.pk}/capturar_assinatura/"
    )
    assert response.status_code == 403


@pytest.mark.django_db(transaction=False)
def test_capturar_assinatura_nao_e_assinante(proposicao):
    """Autor não cadastrado na lista de assinantes retorna 403."""
    _, autor, token = _criar_usuario_com_autor("v3@cmj.go.leg.br", "Vereador C")
    proposicao.autor = autor
    proposicao.save(update_fields=["autor"])
    # Nenhum ProposicaoAssinante criado para este autor
    client = _api_client_para(token)
    response = client.post(
        f"/api/materia/proposicao/{proposicao.pk}/capturar_assinatura/"
    )
    assert response.status_code == 403


@pytest.mark.django_db(transaction=False)
def test_capturar_assinatura_ja_assinado(proposicao):
    """Autor com status 'S' não pode capturar lock novamente (400)."""
    _, autor, token = _criar_usuario_com_autor("v4@cmj.go.leg.br", "Vereador D")
    proposicao.autor = autor
    proposicao.save(update_fields=["autor"])
    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=autor,
        status=ProposicaoAssinante.STATUS_ASSINADO,
        data_assinatura=timezone.now(),
    )

    client = _api_client_para(token)
    response = client.post(
        f"/api/materia/proposicao/{proposicao.pk}/capturar_assinatura/"
    )
    assert response.status_code == 400


@pytest.mark.django_db(transaction=False)
def test_capturar_assinatura_conflito_outro_lock(proposicao):
    """Se outro autor já tem lock ativo, retorna 409 Conflict."""
    _, autor_a, _ = _criar_usuario_com_autor("va@cmj.go.leg.br", "Vereador A")
    _, autor_b, token_b = _criar_usuario_com_autor("vb@cmj.go.leg.br", "Vereador B")
    # Autor B faz a requisição — proposicao precisa estar no queryset dele
    proposicao.autor = autor_b
    proposicao.save(update_fields=["autor"])

    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=autor_a,
        status=ProposicaoAssinante.STATUS_EM_ASSINATURA,
        data_captura=timezone.now(),
    )
    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=autor_b,
        status=ProposicaoAssinante.STATUS_PENDENTE,
    )

    client_b = _api_client_para(token_b)
    response = client_b.post(
        f"/api/materia/proposicao/{proposicao.pk}/capturar_assinatura/"
    )
    assert response.status_code == 409


@pytest.mark.django_db(transaction=False)
def test_capturar_assinatura_libera_lock_expirado(proposicao):
    """Lock expirado (> 5 min) de outro autor é liberado antes de conceder o novo."""
    _, autor_a, _ = _criar_usuario_com_autor("va2@cmj.go.leg.br", "Vereador AX")
    _, autor_b, token_b = _criar_usuario_com_autor("vb2@cmj.go.leg.br", "Vereador BX")
    # Autor B faz a requisição — proposicao precisa estar no queryset dele
    proposicao.autor = autor_b
    proposicao.save(update_fields=["autor"])

    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=autor_a,
        status=ProposicaoAssinante.STATUS_EM_ASSINATURA,
        data_captura=timezone.now() - timedelta(minutes=6),
    )
    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=autor_b,
        status=ProposicaoAssinante.STATUS_PENDENTE,
    )

    client_b = _api_client_para(token_b)
    response = client_b.post(
        f"/api/materia/proposicao/{proposicao.pk}/capturar_assinatura/"
    )
    assert response.status_code == 200

    # Lock do autor A deve ter sido liberado
    pa_a = ProposicaoAssinante.objects.get(proposicao=proposicao, autor=autor_a)
    assert pa_a.status == ProposicaoAssinante.STATUS_PENDENTE
    assert pa_a.data_captura is None

    # Autor B agora tem o lock
    pa_b = ProposicaoAssinante.objects.get(proposicao=proposicao, autor=autor_b)
    assert pa_b.status == ProposicaoAssinante.STATUS_EM_ASSINATURA


# ===========================================================================
#  Testes do endpoint POST liberar_assinatura/
# ===========================================================================


@pytest.mark.django_db(transaction=False)
def test_liberar_assinatura_sucesso(proposicao):
    """Autor com lock ativo libera corretamente → status volta a 'P'."""
    _, autor, token = _criar_usuario_com_autor("vl@cmj.go.leg.br", "Vereador L")
    proposicao.autor = autor
    proposicao.save(update_fields=["autor"])
    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=autor,
        status=ProposicaoAssinante.STATUS_EM_ASSINATURA,
        data_captura=timezone.now(),
    )

    client = _api_client_para(token)
    response = client.post(
        f"/api/materia/proposicao/{proposicao.pk}/liberar_assinatura/"
    )
    assert response.status_code == 200

    pa = ProposicaoAssinante.objects.get(proposicao=proposicao, autor=autor)
    assert pa.status == ProposicaoAssinante.STATUS_PENDENTE
    assert pa.data_captura is None


@pytest.mark.django_db(transaction=False)
def test_liberar_assinatura_sem_lock_ativo(proposicao):
    """Autor sem lock ativo recebe 400 ao tentar liberar."""
    _, autor, token = _criar_usuario_com_autor("vl2@cmj.go.leg.br", "Vereador L2")
    proposicao.autor = autor
    proposicao.save(update_fields=["autor"])
    baker.make(
        ProposicaoAssinante,
        proposicao=proposicao,
        autor=autor,
        status=ProposicaoAssinante.STATUS_PENDENTE,
    )

    client = _api_client_para(token)
    response = client.post(
        f"/api/materia/proposicao/{proposicao.pk}/liberar_assinatura/"
    )
    assert response.status_code == 400


@pytest.mark.django_db(transaction=False)
def test_liberar_assinatura_nao_autenticado(proposicao):
    """Requisição não autenticada retorna 401 ou 403."""
    client = APIClient()
    response = client.post(
        f"/api/materia/proposicao/{proposicao.pk}/liberar_assinatura/"
    )
    assert response.status_code in (401, 403)


# ===========================================================================
#  Testes do endpoint GET minhas_solicitacoes/
# ===========================================================================


@pytest.mark.django_db(transaction=False)
def test_minhas_solicitacoes_retorna_pendentes_e_em_assinatura(tipo_proposicao):
    """Deve retornar proposições com status P ou A, mas não S."""
    _, autor, token = _criar_usuario_com_autor("ms1@cmj.go.leg.br", "Vereador MS1")

    prop_p = baker.make(
        Proposicao, tipo=tipo_proposicao, descricao="Pendente", data_envio=None
    )
    prop_a = baker.make(
        Proposicao, tipo=tipo_proposicao, descricao="Em assinatura", data_envio=None
    )
    prop_s = baker.make(
        Proposicao, tipo=tipo_proposicao, descricao="Já assinada", data_envio=None
    )

    baker.make(
        ProposicaoAssinante,
        proposicao=prop_p,
        autor=autor,
        status=ProposicaoAssinante.STATUS_PENDENTE,
    )
    baker.make(
        ProposicaoAssinante,
        proposicao=prop_a,
        autor=autor,
        status=ProposicaoAssinante.STATUS_EM_ASSINATURA,
        data_captura=timezone.now(),
    )
    baker.make(
        ProposicaoAssinante,
        proposicao=prop_s,
        autor=autor,
        status=ProposicaoAssinante.STATUS_ASSINADO,
        data_assinatura=timezone.now(),
    )

    client = _api_client_para(token)
    response = client.get("/api/materia/proposicao/minhas_solicitacoes/")
    assert response.status_code == 200

    resultados = (
        response.data
        if isinstance(response.data, list)
        else response.data.get("results", response.data)
    )
    ids_retornados = {item["id"] for item in resultados}
    assert prop_p.pk in ids_retornados
    assert prop_a.pk in ids_retornados
    assert prop_s.pk not in ids_retornados


@pytest.mark.django_db(transaction=False)
def test_minhas_solicitacoes_independe_do_autor_principal(tipo_proposicao):
    """Deve retornar proposição mesmo quando proposicao.autor é outro vereador."""
    _, autor_principal, _ = _criar_usuario_com_autor(
        "principal@cmj.go.leg.br", "Autor Principal"
    )
    _, co_signatario, token = _criar_usuario_com_autor(
        "cosig@cmj.go.leg.br", "Co-Signatário"
    )

    prop = baker.make(
        Proposicao,
        tipo=tipo_proposicao,
        autor=autor_principal,  # autor principal é outro
        descricao="Proposição do principal",
        data_envio=None,
    )
    baker.make(
        ProposicaoAssinante,
        proposicao=prop,
        autor=co_signatario,
        status=ProposicaoAssinante.STATUS_PENDENTE,
    )

    client = _api_client_para(token)
    response = client.get("/api/materia/proposicao/minhas_solicitacoes/")
    assert response.status_code == 200
    resultados = (
        response.data
        if isinstance(response.data, list)
        else response.data.get("results", response.data)
    )
    ids_retornados = {item["id"] for item in resultados}
    assert prop.pk in ids_retornados


@pytest.mark.django_db(transaction=False)
def test_minhas_solicitacoes_nao_retorna_de_outros_autores(tipo_proposicao):
    """Não deve retornar proposições onde o usuário não é co-signatário."""
    _, autor_a, token_a = _criar_usuario_com_autor("aa@cmj.go.leg.br", "Autor A")
    _, autor_b, _ = _criar_usuario_com_autor("ab@cmj.go.leg.br", "Autor B")

    prop_de_b = baker.make(
        Proposicao, tipo=tipo_proposicao, descricao="Prop de B", data_envio=None
    )
    baker.make(
        ProposicaoAssinante,
        proposicao=prop_de_b,
        autor=autor_b,
        status=ProposicaoAssinante.STATUS_PENDENTE,
    )

    client_a = _api_client_para(token_a)
    response = client_a.get("/api/materia/proposicao/minhas_solicitacoes/")
    assert response.status_code == 200
    resultados = (
        response.data
        if isinstance(response.data, list)
        else response.data.get("results", response.data)
    )
    ids_retornados = {item["id"] for item in resultados}
    assert prop_de_b.pk not in ids_retornados


@pytest.mark.django_db(transaction=False)
def test_minhas_solicitacoes_sem_autor_retorna_403():
    """Usuário sem Autor vinculado recebe 403."""
    _, token = _criar_usuario_sem_autor("noautor@cmj.go.leg.br")
    client = _api_client_para(token)
    response = client.get("/api/materia/proposicao/minhas_solicitacoes/")
    assert response.status_code == 403


@pytest.mark.django_db(transaction=False)
def test_minhas_solicitacoes_nao_autenticado():
    """Requisição sem token retorna 401 ou 403."""
    client = APIClient()
    response = client.get("/api/materia/proposicao/minhas_solicitacoes/")
    assert response.status_code in (401, 403)


# ===========================================================================
#  Testes do endpoint GET texto_original/ para co-signatários
# ===========================================================================


@pytest.mark.django_db(transaction=False)
def test_texto_original_acessivel_para_co_signatario_pendente(tipo_proposicao):
    """
    Co-signatário com status P deve encontrar a proposição no queryset de
    texto_original, mesmo que proposicao.autor seja outro vereador.

    Usa mock em response_file para isolar o comportamento do queryset:
    sem arquivo físico, "404 objeto-não-encontrado" e "404 sem-arquivo"
    produzem a mesma resposta HTTP. O mock retorna HttpResponse direto,
    bypassando o renderer DRF (como o response_file real faz).
    """
    from unittest.mock import patch

    from django.http import HttpResponse, HttpResponseNotFound

    from sapl.api.mixins import ResponseFileMixin

    _, autor_principal, _ = _criar_usuario_com_autor(
        "tp1@cmj.go.leg.br", "Autor Principal TP"
    )
    _, co_signatario, token = _criar_usuario_com_autor(
        "tp2@cmj.go.leg.br", "Co-Signatário TP"
    )

    prop = baker.make(
        Proposicao,
        tipo=tipo_proposicao,
        autor=autor_principal,
        descricao="Proposição para assinar",
        data_envio=None,
    )
    baker.make(
        ProposicaoAssinante,
        proposicao=prop,
        autor=co_signatario,
        status=ProposicaoAssinante.STATUS_PENDENTE,
    )

    def mock_rf(self_vs, request, *args, **kwargs):
        item = self_vs.get_queryset().filter(pk=kwargs["pk"]).first()
        if not item:
            return HttpResponseNotFound()
        return HttpResponse(b"mock", content_type="application/octet-stream")

    client = _api_client_para(token)
    with patch.object(ResponseFileMixin, "response_file", mock_rf):
        response = client.get(f"/api/materia/proposicao/{prop.pk}/texto_original/")

    assert response.status_code == 200


@pytest.mark.django_db(transaction=False)
def test_texto_original_inacessivel_para_co_signatario_ja_assinado(tipo_proposicao):
    """
    Co-signatário com status S (já assinou) não recebe acesso extra via
    texto_original — a proposição não é incluída no queryset.
    """
    from unittest.mock import patch

    from django.http import HttpResponse, HttpResponseNotFound

    from sapl.api.mixins import ResponseFileMixin

    _, autor_principal, _ = _criar_usuario_com_autor("ts1@cmj.go.leg.br", "Autor TS1")
    _, co_signatario_assinado, token = _criar_usuario_com_autor(
        "ts2@cmj.go.leg.br", "Co-Sig Assinado"
    )

    prop = baker.make(
        Proposicao,
        tipo=tipo_proposicao,
        autor=autor_principal,
        descricao="Proposição já assinada por todos",
        data_envio=None,
    )
    baker.make(
        ProposicaoAssinante,
        proposicao=prop,
        autor=co_signatario_assinado,
        status=ProposicaoAssinante.STATUS_ASSINADO,
        data_assinatura=timezone.now(),
    )

    def mock_rf(self_vs, request, *args, **kwargs):
        item = self_vs.get_queryset().filter(pk=kwargs["pk"]).first()
        if not item:
            return HttpResponseNotFound()
        return HttpResponse(b"mock", content_type="application/octet-stream")

    client = _api_client_para(token)
    with patch.object(ResponseFileMixin, "response_file", mock_rf):
        response = client.get(f"/api/materia/proposicao/{prop.pk}/texto_original/")

    assert response.status_code == 404
