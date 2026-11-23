"""Campos devolvidos e ``expand`` nas rotas geradas (docs/specs/api/serializacao.md)."""

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from model_bakery import baker
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory

from cmj.core.models import AreaTrabalho
from drfautoapi.drfautoapi import ApiViewSetConstrutor
from sapl.api.serializers import ParlamentarSerializer
from sapl.base.models import Autor, OperadorAutor
from sapl.compilacao.models import Nota, TextoArticulado
from sapl.materia.models import MateriaLegislativa, Proposicao, Tramitacao
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Filiacao, Parlamentar
from sapl.protocoloadm.models import (
    Anexado,
    DocumentoAdministrativo,
    TipoDocumentoAdministrativo,
    TramitacaoAdministrativo,
)
from sapl.sessao.models import RegistroLeitura, RegistroVotacao, VotoParlamentar

CAMPOS_PESSOAIS = set(ParlamentarSerializer.CAMPOS_PESSOAIS)


@pytest.fixture
def filiacao():
    parlamentar = baker.make(
        Parlamentar,
        nome_completo="Parlamentar de Teste",
        nome_parlamentar="Parlamentar",
        cpf="000.000.000-00",
        rg="0000000",
        endereco_residencia="Rua de Teste, 1",
    )
    return baker.make(Filiacao, parlamentar=parlamentar)


@pytest.fixture
def anonimo():
    return APIClient()


@pytest.fixture
def sem_permissao(django_user_model):
    client = APIClient()
    client.force_authenticate(
        user=django_user_model.objects.create_user(
            email="sem-permissao@exemplo.invalid", password="senha-de-teste-123"
        )
    )
    return client


@pytest.fixture
def superusuario(django_user_model):
    client = APIClient()
    client.force_authenticate(
        user=django_user_model.objects.create_superuser(
            email="superusuario@exemplo.invalid", password="senha-de-teste-123"
        )
    )
    return client


def _parlamentar_pela_rota(client, filiacao):
    resposta = client.get(f"/api/parlamentares/parlamentar/{filiacao.parlamentar_id}/")
    assert resposta.status_code == 200
    return resposta.json()


def _parlamentar_por_expand(client, filiacao):
    resposta = client.get(
        f"/api/parlamentares/filiacao/{filiacao.pk}/", {"expand": "parlamentar"}
    )
    assert resposta.status_code == 200
    return resposta.json()["parlamentar"]


@pytest.mark.django_db
@pytest.mark.spec("API-SER-027")
@pytest.mark.parametrize("cliente", ["anonimo", "sem_permissao"])
@pytest.mark.parametrize("caminho", [_parlamentar_pela_rota, _parlamentar_por_expand])
def test_parlamentar_sai_sem_campos_pessoais_para_quem_nao_cadastra(
    request, cliente, caminho, filiacao
):
    parlamentar = caminho(request.getfixturevalue(cliente), filiacao)

    assert parlamentar["nome_parlamentar"] == "Parlamentar"
    assert not CAMPOS_PESSOAIS & set(parlamentar)
    assert {"data_nascimento", "sexo"} <= CAMPOS_PESSOAIS
    # o contato do mandato, que a tela pública mostra, continua saindo
    assert {"email", "telefone"} <= set(parlamentar)


@pytest.mark.django_db
@pytest.mark.spec("API-SER-027")
@pytest.mark.parametrize("caminho", [_parlamentar_pela_rota, _parlamentar_por_expand])
def test_parlamentar_sai_completo_para_quem_cadastra(superusuario, caminho, filiacao):
    parlamentar = caminho(superusuario, filiacao)

    assert CAMPOS_PESSOAIS <= set(parlamentar)
    assert parlamentar["cpf"] == "000.000.000-00"


@pytest.mark.django_db
@pytest.mark.spec("API-SER-025")
def test_expand_segue_a_permissao_de_leitura_do_model_relacionado(
    anonimo, sem_permissao, superusuario, filiacao
):
    url = f"/api/parlamentares/filiacao/{filiacao.pk}/"
    params = {"expand": "parlamentar;partido"}

    for client in (anonimo, sem_permissao):
        item = client.get(url, params).json()
        # parlamentar tem rota de leitura pública; partido, não
        assert item["parlamentar"]["id"] == filiacao.parlamentar_id
        assert item["partido"] == filiacao.partido_id

    item = superusuario.get(url, params).json()
    assert item["parlamentar"]["id"] == filiacao.parlamentar_id
    assert item["partido"]["id"] == filiacao.partido_id


@pytest.fixture
def anexacao_com_documento_de_area_restrita():
    publica = baker.make(AreaTrabalho, tipo=AreaTrabalho.TIPO_PUBLICO)
    restrita = baker.make(AreaTrabalho, tipo=AreaTrabalho.TIPO_PROCURADORIA)
    tipo = baker.make(TipoDocumentoAdministrativo, workspace=publica)
    principal = baker.make(
        DocumentoAdministrativo, tipo=tipo, workspace=publica, numero=1, ano=2026
    )
    anexado = baker.make(
        DocumentoAdministrativo, tipo=tipo, workspace=restrita, numero=2, ano=2026
    )
    return baker.make(Anexado, documento_principal=principal, documento_anexado=anexado)


@pytest.mark.django_db
@pytest.mark.spec("API-SER-026")
def test_expand_segue_a_visibilidade_do_model_relacionado(
    anonimo, anexacao_com_documento_de_area_restrita
):
    anexacao = anexacao_com_documento_de_area_restrita

    item = anonimo.get(
        f"/api/protocoloadm/anexado/{anexacao.pk}/",
        {"expand": "documento_principal;documento_anexado"},
    ).json()

    # o documento da área pública expande; o da área restrita segue como id
    assert item["documento_principal"]["id"] == anexacao.documento_principal_id
    assert item["documento_anexado"] == anexacao.documento_anexado_id


MODELS_QUE_GUARDAM_QUEM_REGISTROU = [
    MateriaLegislativa,
    Proposicao,
    Tramitacao,
    NormaJuridica,
    TramitacaoAdministrativo,
    RegistroLeitura,
    RegistroVotacao,
    VotoParlamentar,
]


def _campos_do_serializer(model, user=None):
    """Campos que o serializer da rota do model entrega ao usuário; sem
    usuário, o serializer é montado sem requisição."""
    reverse("sapl.api:core_areatrabalho-list")  # carrega as rotas da API
    serializer_class = ApiViewSetConstrutor.get_viewset_for_model(
        model
    ).serializer_class
    if user is None:
        return set(serializer_class().fields)
    request = Request(APIRequestFactory().get("/api/"))
    request.user = user
    return set(serializer_class(context={"request": request}).fields)


@pytest.mark.django_db
@pytest.mark.spec("API-SER-028")
@pytest.mark.parametrize("model", MODELS_QUE_GUARDAM_QUEM_REGISTROU)
def test_ip_e_user_do_registro_so_saem_para_superusuario(model, django_user_model):
    comum = django_user_model.objects.create_user(
        email="comum@exemplo.invalid", password="senha-de-teste-123"
    )
    superuser = django_user_model.objects.create_superuser(
        email="super@exemplo.invalid", password="senha-de-teste-123"
    )

    assert {"ip", "user"} <= _campos_do_serializer(model, superuser)
    for campos in (
        _campos_do_serializer(model, AnonymousUser()),
        _campos_do_serializer(model, comum),
        _campos_do_serializer(model),
    ):
        assert not {"ip", "user"} & campos
        assert "id" in campos


def _usuario_com_permissoes(django_user_model, model, *acoes):
    """Usuário comum com as permissões indicadas do model."""
    user = django_user_model.objects.create_user(
        email=f"operador-{model._meta.model_name}@exemplo.invalid",
        password="senha-de-teste-123",
    )
    content_type = ContentType.objects.get_for_model(model)
    for acao in acoes:
        codename = f"{acao}_{model._meta.model_name}"
        permission, _ = Permission.objects.get_or_create(
            codename=codename, content_type=content_type, defaults={"name": codename}
        )
        user.user_permissions.add(permission)
    return django_user_model.objects.get(pk=user.pk)  # limpa o cache de permissões


@pytest.mark.django_db
@pytest.mark.spec("API-SER-028", "API-SER-032")
def test_user_sem_ip_segue_a_permissao_de_listagem(django_user_model):
    operador = _usuario_com_permissoes(django_user_model, OperadorAutor, "list")

    assert "user" in _campos_do_serializer(OperadorAutor, operador)
    assert "user" not in _campos_do_serializer(Tramitacao, operador)


@pytest.mark.django_db
@pytest.mark.spec("API-SER-032")
@pytest.mark.parametrize(
    "model, campo",
    [(Autor, "operadores"), (Nota, "owner"), (TextoArticulado, "owners")],
)
def test_relacao_com_usuario_so_sai_para_quem_lista_o_model(
    model, campo, django_user_model
):
    comum = django_user_model.objects.create_user(
        email="comum@exemplo.invalid", password="senha-de-teste-123"
    )
    lista = _usuario_com_permissoes(django_user_model, model, "list")
    superuser = django_user_model.objects.create_superuser(
        email="super@exemplo.invalid", password="senha-de-teste-123"
    )

    assert campo in _campos_do_serializer(model, lista)
    assert campo in _campos_do_serializer(model, superuser)
    for campos in (
        _campos_do_serializer(model, AnonymousUser()),
        _campos_do_serializer(model, comum),
        _campos_do_serializer(model),
    ):
        assert campo not in campos
        assert "id" in campos


@pytest.mark.django_db
@pytest.mark.spec("API-SER-033")
def test_owner_e_modifier_vem_do_usuario_da_requisicao(django_user_model):
    criador = django_user_model.objects.create_superuser(
        email="criador@exemplo.invalid", password="senha-de-teste-123"
    )
    editor = django_user_model.objects.create_superuser(
        email="editor@exemplo.invalid", password="senha-de-teste-123"
    )
    outro = django_user_model.objects.create_user(
        email="outro@exemplo.invalid", password="senha-de-teste-123"
    )
    rota = "/api/core/areatrabalho/"

    client = APIClient()
    client.force_authenticate(user=criador)
    resposta = client.post(
        rota,
        {"nome": "Área", "descricao": "Área", "owner": outro.pk, "modifier": outro.pk},
        format="json",
    )
    assert resposta.status_code == 201
    area = AreaTrabalho.objects.get(pk=resposta.json()["id"])
    assert (area.owner, area.modifier) == (criador, criador)

    client.force_authenticate(user=editor)
    resposta = client.patch(
        f"{rota}{area.pk}/", {"nome": "Área alterada", "owner": outro.pk}, format="json"
    )
    assert resposta.status_code == 200
    area.refresh_from_db()
    assert area.nome == "Área alterada"
    assert (area.owner, area.modifier) == (criador, editor)


@pytest.mark.django_db
@pytest.mark.spec("API-SER-028")
def test_norma_sai_sem_ip_e_user_e_nao_e_filtrada_por_eles(
    anonimo, superusuario, django_user_model
):
    registrou = django_user_model.objects.create_user(
        email="registrou@exemplo.invalid", password="senha-de-teste-123"
    )
    norma = baker.make(NormaJuridica, user=registrou, ip="192.0.2.10")
    baker.make(NormaJuridica, user=None, ip="")
    rota = "/api/norma/normajuridica/"

    for url in (rota, f"{rota}?include=id,ip,user", f"{rota}{norma.pk}/"):
        resposta = anonimo.get(url).json()
        item = resposta["results"][0] if "results" in resposta else resposta
        assert "ip" not in item and "user" not in item

    item = superusuario.get(f"{rota}{norma.pk}/").json()
    assert item["ip"] == "192.0.2.10" and item["user"] == registrou.pk

    filtros = (f"user={registrou.pk}", "ip=192.0.2.10", "user=0", "o=user,ip")
    for filtro in filtros:
        resposta = anonimo.get(f"{rota}?{filtro}")
        assert resposta.status_code == 200
        assert resposta.json()["pagination"]["total_entries"] == 2

    resposta = superusuario.get(f"{rota}?user={registrou.pk}")
    assert resposta.json()["pagination"]["total_entries"] == 1


@pytest.mark.django_db
@pytest.mark.spec("API-SER-029")
def test_metadata_sai_sem_as_chaves_de_armazenamento(
    anonimo, sem_permissao, superusuario
):
    arquivo = {"path": "caminho/interno.pdf", "hash": "abc"}
    completo = {
        "s3_aws": {"texto_integral": arquivo},
        "s3_cmj": {"texto_integral": arquivo},
        "locaweb": {"texto_integral": arquivo},
        "selos": {"cert_protocolo": {"x": 1}},
    }
    norma = baker.make(NormaJuridica)
    NormaJuridica.objects.filter(pk=norma.pk).update(metadata=completo)
    rota = "/api/norma/normajuridica/"

    for client in (anonimo, sem_permissao):
        assert client.get(f"{rota}{norma.pk}/").json()["metadata"] == {
            "selos": {"cert_protocolo": {"x": 1}}
        }
        assert client.get(rota).json()["results"][0]["metadata"] == {
            "selos": {"cert_protocolo": {"x": 1}}
        }

    assert superusuario.get(f"{rota}{norma.pk}/").json()["metadata"] == completo

    norma.refresh_from_db()
    serializer_class = ApiViewSetConstrutor.get_viewset_for_model(
        NormaJuridica
    ).serializer_class
    assert set(serializer_class(norma).data["metadata"]) == {"selos"}
    assert norma.metadata == completo


@pytest.mark.django_db
@pytest.mark.spec("API-SER-034")
def test_gravacao_de_metadata_mantem_as_chaves_de_armazenamento(django_user_model):
    arquivo = {"path": "caminho/interno.pdf", "hash": "abc"}
    gravado = {"s3_aws": {"texto_integral": arquivo}, "selos": {"a": 1}}
    norma = baker.make(NormaJuridica)
    NormaJuridica.objects.filter(pk=norma.pk).update(metadata=gravado)
    rota = f"/api/norma/normajuridica/{norma.pk}/"
    enviado = {"selos": {"a": 2}, "s3_aws": {"outro": 1}, "s3_cmj": {"outro": 1}}

    operador = APIClient()
    operador.force_authenticate(
        user=_usuario_com_permissoes(
            django_user_model, NormaJuridica, "list", "detail", "change"
        )
    )
    assert operador.patch(rota, {"metadata": enviado}, format="json").status_code == 200
    norma.refresh_from_db()
    assert norma.metadata == {"selos": {"a": 2}, "s3_aws": {"texto_integral": arquivo}}

    superuser = APIClient()
    superuser.force_authenticate(
        user=django_user_model.objects.create_superuser(
            email="super@exemplo.invalid", password="senha-de-teste-123"
        )
    )
    assert (
        superuser.patch(rota, {"metadata": enviado}, format="json").status_code == 200
    )
    norma.refresh_from_db()
    assert norma.metadata == enviado


@pytest.mark.django_db
@pytest.mark.spec("API-SER-036")
def test_documento_administrativo_segue_o_que_a_tela_mostra(
    anonimo, superusuario, django_user_model
):
    internos = {"link_share", "old_path", "old_json", "temp_migracao_sislegis"}
    area = baker.make(AreaTrabalho, tipo=AreaTrabalho.TIPO_PUBLICO)
    documento = baker.make(
        DocumentoAdministrativo,
        tipo=baker.make(TipoDocumentoAdministrativo, workspace=area),
        workspace=area,
        numero=1,
        ano=2026,
        interessado="Pessoa interessada",
        email="interessada@exemplo.invalid",
        old_path="caminho/antigo",
        old_json={"id": 1},
    )
    rota = "/api/protocoloadm/documentoadministrativo/"

    for url in (
        rota,
        f"{rota}?include=id,link_share,old_json",
        f"{rota}{documento.pk}/",
    ):
        resposta = anonimo.get(url).json()
        item = resposta["results"][0] if "results" in resposta else resposta
        assert not internos & set(item)
    item = anonimo.get(f"{rota}{documento.pk}/").json()
    assert item["interessado"] == "Pessoa interessada"
    assert item["email"] == "interessada@exemplo.invalid"

    resposta = anonimo.get(f"{rota}?old_path__isnull=true&o=old_path")
    assert resposta.json()["pagination"]["total_entries"] == 1

    lista = APIClient()
    lista.force_authenticate(
        user=_usuario_com_permissoes(django_user_model, DocumentoAdministrativo, "list")
    )
    for client in (lista, superusuario):
        assert internos <= set(client.get(f"{rota}{documento.pk}/").json())


URL_FILIACAO = "/api/parlamentares/filiacao/"


@pytest.mark.django_db
@pytest.mark.spec("API-SER-037")
@pytest.mark.parametrize(
    "expand",
    [
        "a;b;c;d;e;f;g;h;i",
        # cada alternativa separada por vírgula num nível conta um caminho
        "parlamentar.a,b,c,d,e;partido.f,g,h,i",
        "a,b,c.d,e,f",
    ],
)
def test_expand_com_mais_caminhos_que_o_teto_responde_400(filiacao, expand):
    for url in (URL_FILIACAO, f"{URL_FILIACAO}{filiacao.pk}/"):
        resposta = APIClient().get(url, {"expand": expand})

        assert resposta.status_code == 400
        assert "expand" in resposta.json()


@pytest.mark.django_db
@pytest.mark.spec("API-SER-037")
@pytest.mark.parametrize(
    "expand",
    [
        "parlamentar;partido",
        "a;b;c;d;e;f;g;h",
        "parlamentar.a,b,c,d;partido.e,f,g,h",
    ],
)
def test_expand_ate_o_teto_de_caminhos_e_atendido(filiacao, expand):
    resposta = APIClient().get(URL_FILIACAO, {"expand": expand})

    assert resposta.status_code == 200
    expandido = isinstance(resposta.json()["results"][0]["parlamentar"], dict)
    assert expandido is expand.startswith("parlamentar")
