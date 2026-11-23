"""Resposta condicional das rotas geradas (docs/specs/api/gerador.md)."""

from datetime import date, timedelta

import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.http import http_date
from model_bakery import baker
from rest_framework.test import APIClient

from cmj.core.models import AuditLog
from sapl.materia.models import MateriaLegislativa, Proposicao, TipoMateriaLegislativa

ROTA = "/api/materia/tipomaterialegislativa/"
FUTURO = "Fri, 01 Jan 2100 00:00:00 GMT"


AGORA = timezone.now().replace(microsecond=0)


def _ha(**tempo):
    """Um instante fixo, contado da carga do módulo."""
    return AGORA - timedelta(**tempo)


def _auditar(obj, operacao="U", quando=None, app=None):
    """Um registro de auditoria de ``obj``, como o signal grava, na data dada."""
    excluido = operacao in ("D", "P")
    registro = AuditLog.objects.create(
        operation=operacao,
        obj_id=obj.pk,
        app_name=app or obj._meta.app_label,
        model_name=obj._meta.model_name,
        content_type=None if excluido else ContentType.objects.get_for_model(obj),
        object_id=None if excluido else obj.pk,
    )
    AuditLog.objects.filter(pk=registro.pk).update(timestamp=quando or _ha(hours=1))
    return registro


@pytest.fixture
def tipo():
    """Um tipo de matéria cuja única auditoria é a de uma hora atrás."""
    tipo = baker.make(TipoMateriaLegislativa, sigla="PL", descricao="Projeto de Lei")
    AuditLog.objects.all().delete()
    _auditar(tipo, "C", _ha(hours=1))
    return tipo


@pytest.fixture
def superusuario(django_user_model):
    return django_user_model.objects.create_superuser(
        email="superusuario@exemplo.invalid", password="senha-de-teste-123"
    )


def _get(url, client=None, **cabecalhos):
    return (client or APIClient()).get(url, **cabecalhos)


@pytest.mark.django_db
@pytest.mark.spec("API-GER-031", "API-GER-035")
@pytest.mark.parametrize("url", [ROTA, ROTA + "{pk}/"])
def test_lista_e_detalhe_levam_a_data_e_respondem_304_a_quem_ja_tem_a_resposta(
    tipo, url
):
    url = url.format(pk=tipo.pk)

    resposta = _get(url)

    assert resposta.status_code == 200
    assert resposta["Last-Modified"] == http_date(_ha(hours=1).timestamp())
    assert resposta["Cache-Control"] == "private, no-cache"

    revalidada = _get(url, HTTP_IF_MODIFIED_SINCE=resposta["Last-Modified"])
    assert revalidada.status_code == 304
    assert revalidada.content == b""
    assert revalidada["Last-Modified"] == resposta["Last-Modified"]

    antiga = _get(url, HTTP_IF_MODIFIED_SINCE=http_date(_ha(hours=2).timestamp()))
    assert antiga.status_code == 200


@pytest.mark.django_db
@pytest.mark.spec("API-GER-031")
@pytest.mark.parametrize("url", ["/api/agenda/evento/", "/api/agenda/evento/1/"])
def test_sem_permissao_nao_ha_data_nem_304(url):
    resposta = _get(url, HTTP_IF_MODIFIED_SINCE=FUTURO)

    assert resposta.status_code == 401
    assert "Last-Modified" not in resposta


@pytest.mark.django_db
@pytest.mark.spec("API-GER-031")
def test_escrita_e_action_nao_passam_pela_resposta_condicional(tipo, superusuario):
    client = APIClient()
    client.force_authenticate(superusuario)

    alteracao = client.patch(
        f"{ROTA}{tipo.pk}/",
        {"descricao": "Outro nome"},
        HTTP_IF_UNMODIFIED_SINCE=http_date(_ha(hours=2).timestamp()),
    )
    assert alteracao.status_code == 200
    assert "Last-Modified" not in alteracao

    materia = baker.make(
        MateriaLegislativa, tipo=tipo, data_apresentacao=date(2020, 1, 1)
    )
    MateriaLegislativa.objects.update(data_ultima_atualizacao=_ha(hours=1))
    action = _get(
        f"/api/materia/materialegislativa/{materia.pk}/anexadas/",
        HTTP_IF_MODIFIED_SINCE=FUTURO,
    )
    assert action.status_code == 200
    assert "Last-Modified" not in action


@pytest.mark.django_db
@pytest.mark.spec("API-GER-032")
def test_data_do_detalhe_e_a_do_proprio_registro(tipo):
    outro = baker.make(TipoMateriaLegislativa, sigla="PR", descricao="Resolução")
    AuditLog.objects.filter(obj_id=outro.pk).delete()
    _auditar(outro, "U", _ha(minutes=10))

    assert _get(f"{ROTA}{tipo.pk}/")["Last-Modified"] == http_date(
        _ha(hours=1).timestamp()
    )
    assert _get(f"{ROTA}{outro.pk}/")["Last-Modified"] == http_date(
        _ha(minutes=10).timestamp()
    )


@pytest.mark.django_db
@pytest.mark.spec("API-GER-032")
def test_registro_que_nao_existe_responde_404_sem_data(tipo):
    pk = tipo.pk
    tipo.delete()

    resposta = _get(f"{ROTA}{pk}/", HTTP_IF_MODIFIED_SINCE=FUTURO)

    assert resposta.status_code == 404
    assert "Last-Modified" not in resposta


@pytest.mark.django_db
@pytest.mark.spec("API-GER-032", "API-GER-033")
def test_auditoria_de_model_de_mesmo_nome_em_outro_app_nao_conta(tipo):
    # mesmo nome de model e mesmo id, em outro app
    _auditar(tipo, "D", _ha(minutes=5), app="outroapp")
    AuditLog.objects.create(
        operation="U",
        obj_id=tipo.pk,
        app_name="outroapp",
        model_name="tipomaterialegislativa",
        content_type=ContentType.objects.get_for_model(AuditLog),
        object_id=tipo.pk,
    )
    AuditLog.objects.filter(app_name="outroapp").update(timestamp=_ha(minutes=5))

    esperado = http_date(_ha(hours=1).timestamp())
    assert _get(ROTA)["Last-Modified"] == esperado
    assert _get(f"{ROTA}{tipo.pk}/")["Last-Modified"] == esperado


@pytest.mark.django_db
@pytest.mark.spec("API-GER-033")
def test_data_da_lista_e_a_do_model_e_muda_com_exclusao(tipo):
    primeira = _get(ROTA + "?sigla=PL")
    assert primeira["Last-Modified"] == http_date(_ha(hours=1).timestamp())

    # a exclusão de outro registro, auditada há dez minutos
    outro = baker.make(TipoMateriaLegislativa, sigla="PR", descricao="Resolução")
    TipoMateriaLegislativa.objects.filter(pk=outro.pk).delete()
    AuditLog.objects.filter(obj_id=outro.pk).delete()
    _auditar(outro, "D", _ha(minutes=10))

    # a data vale para qualquer lista do model, filtrada ou não
    for url in (ROTA, ROTA + "?sigla=PL"):
        depois = _get(url, HTTP_IF_MODIFIED_SINCE=primeira["Last-Modified"])
        assert depois.status_code == 200
        assert depois["Last-Modified"] == http_date(_ha(minutes=10).timestamp())


@pytest.mark.django_db
@pytest.mark.spec("API-GER-033")
def test_registro_de_pesquisa_nao_muda_a_data_da_lista(tipo):
    _auditar(tipo, "P", _ha(minutes=5))

    assert _get(ROTA)["Last-Modified"] == http_date(_ha(hours=1).timestamp())


@pytest.mark.django_db
@pytest.mark.spec("API-GER-034")
def test_requisicao_com_expand_nao_tem_resposta_condicional(tipo):
    resposta = _get(
        ROTA + "?expand=sequencia_regimental", HTTP_IF_MODIFIED_SINCE=FUTURO
    )

    assert resposta.status_code == 200
    assert "Last-Modified" not in resposta


@pytest.mark.django_db
@pytest.mark.spec("API-GER-034")
def test_rota_com_visibilidade_por_registro_nao_tem_resposta_condicional(
    superusuario,
):
    proposicao = baker.make(Proposicao, descricao="Proposição", data_envio=_ha(days=1))
    AuditLog.objects.all().delete()
    _auditar(proposicao, "U", _ha(hours=1))
    client = APIClient()
    client.force_authenticate(superusuario)

    for url in (
        "/api/materia/proposicao/",
        f"/api/materia/proposicao/{proposicao.pk}/",
    ):
        resposta = _get(url, client, HTTP_IF_MODIFIED_SINCE=FUTURO)
        assert resposta.status_code == 200
        assert "Last-Modified" not in resposta


@pytest.mark.django_db
@pytest.mark.spec("API-GER-034")
def test_model_sem_auditoria_nao_tem_resposta_condicional():
    baker.make(TipoMateriaLegislativa, sigla="PL", descricao="Projeto de Lei")
    AuditLog.objects.all().delete()

    resposta = _get(ROTA, HTTP_IF_MODIFIED_SINCE=FUTURO)

    assert resposta.status_code == 200
    assert "Last-Modified" not in resposta


@pytest.mark.django_db
@pytest.mark.spec("API-GER-034")
def test_gravacao_no_mesmo_segundo_nao_tem_resposta_condicional(tipo):
    _auditar(tipo, "U", timezone.now())

    resposta = _get(ROTA, HTTP_IF_MODIFIED_SINCE=FUTURO)

    assert resposta.status_code == 200
    assert "Last-Modified" not in resposta


@pytest.mark.django_db
@pytest.mark.spec("API-GER-036")
def test_materia_usa_a_maior_data_entre_a_auditoria_e_a_da_propria_materia(tipo):
    antiga, recente = baker.make(
        MateriaLegislativa, tipo=tipo, data_apresentacao=date(2020, 1, 1), _quantity=2
    )
    AuditLog.objects.all().delete()
    _auditar(antiga, "U", _ha(minutes=30))
    por_pk = MateriaLegislativa.objects.filter
    por_pk(pk=antiga.pk).update(data_ultima_atualizacao=_ha(hours=3))
    por_pk(pk=recente.pk).update(data_ultima_atualizacao=_ha(minutes=20))
    rota = "/api/materia/materialegislativa/"

    # lista: a maior do model; detalhe: a maior da própria matéria
    assert _get(rota)["Last-Modified"] == http_date(_ha(minutes=20).timestamp())
    assert _get(f"{rota}{antiga.pk}/")["Last-Modified"] == http_date(
        _ha(minutes=30).timestamp()
    )
    assert _get(f"{rota}{recente.pk}/")["Last-Modified"] == http_date(
        _ha(minutes=20).timestamp()
    )


@pytest.mark.django_db
@pytest.mark.spec("API-GER-037")
def test_filtro_invalido_na_materia_responde_400():
    resposta = _get("/api/materia/materialegislativa/?ano=abc")

    assert resposta.status_code == 400
    assert "ano" in resposta.json()
