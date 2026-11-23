"""Acesso às rotas geradas da API (docs/specs/api/acesso.md)."""

from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient, APIRequestFactory

from cmj.agenda.models import Evento
from cmj.arq.models import Draft, DraftMidia
from cmj.core.models import AreaTrabalho, AuditLog, OperadorAreaTrabalho
from cmj.loa.models import Loa
from cmj.search.models import ChatMessage, ChatSession
from drfautoapi.drfautoapi import ApiViewSetConstrutor
from sapl.api.permissions import ContainerPermission
from sapl.base.models import Autor, OperadorAutor, TipoAutor
from sapl.comissoes.models import Comissao
from sapl.compilacao.models import (
    NPUBL,
    STATUS_TA_EDITION,
    Dispositivo,
    Nota,
    Publicacao,
    TextoArticulado,
    Vide,
)
from sapl.materia.models import TipoMateriaLegislativa, TipoProposicao
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import (
    DocumentoAdministrativo,
    StatusTramitacaoAdministrativo,
    TipoDocumentoAdministrativo,
)

ROTAS_DE_DOCUMENTO_ADMINISTRATIVO = [
    "/api/protocoloadm/tipodocumentoadministrativo/",
    "/api/protocoloadm/documentoadministrativo/",
    "/api/protocoloadm/documentoacessorioadministrativo/",
    "/api/protocoloadm/tramitacaoadministrativo/",
    "/api/protocoloadm/anexado/",
]
METODOS_DE_LEITURA = ["get", "head", "options"]
METODOS_DE_ESCRITA = ["post", "put", "patch", "delete"]


class _ViewComContainerPermission:
    """O mínimo que ``ContainerPermission`` consulta num viewset."""

    queryset = TipoDocumentoAdministrativo.objects.all()

    def get_queryset(self):
        return self.queryset


def _permite(metodo, user):
    request = getattr(APIRequestFactory(), metodo)("/api/")
    request.user = user
    return ContainerPermission().has_permission(request, _ViewComContainerPermission())


def _url(rota, metodo):
    return rota if metodo == "post" else f"{rota}1/"


@pytest.fixture
def usuario_sem_permissao(django_user_model):
    return django_user_model.objects.create_user(
        email="sem-permissao@exemplo.invalid", password="senha-de-teste-123"
    )


@pytest.fixture
def superusuario(django_user_model):
    return django_user_model.objects.create_superuser(
        email="superusuario@exemplo.invalid", password="senha-de-teste-123"
    )


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-030")
@pytest.mark.parametrize("metodo", METODOS_DE_LEITURA)
def test_container_permission_libera_a_leitura_sem_permissao_de_model(
    metodo, usuario_sem_permissao
):
    assert _permite(metodo, AnonymousUser())
    assert _permite(metodo, usuario_sem_permissao)


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-030")
@pytest.mark.parametrize("metodo", METODOS_DE_ESCRITA)
def test_container_permission_exige_permissao_de_model_na_escrita(
    metodo, usuario_sem_permissao, superusuario
):
    assert not _permite(metodo, AnonymousUser())
    assert not _permite(metodo, usuario_sem_permissao)
    assert _permite(metodo, superusuario)


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-031")
@pytest.mark.parametrize("rota", ROTAS_DE_DOCUMENTO_ADMINISTRATIVO)
def test_rotas_de_documento_administrativo_respondem_a_leitura(rota):
    resposta = APIClient().get(rota)

    assert resposta.status_code == 200
    assert resposta.json()["results"] == []


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-031")
@pytest.mark.parametrize("rota", ROTAS_DE_DOCUMENTO_ADMINISTRATIVO)
@pytest.mark.parametrize("metodo", METODOS_DE_ESCRITA)
def test_rotas_de_documento_administrativo_nao_aceitam_escrita(
    rota, metodo, usuario_sem_permissao, superusuario
):
    dados = {"sigla": "TST", "descricao": "Tipo de teste"}

    anonimo = APIClient()
    assert getattr(anonimo, metodo)(_url(rota, metodo), dados).status_code == 401

    sem_permissao = APIClient()
    sem_permissao.force_authenticate(user=usuario_sem_permissao)
    resposta = getattr(sem_permissao, metodo)(_url(rota, metodo), dados)
    assert resposta.status_code == 403

    com_permissao = APIClient()
    com_permissao.force_authenticate(user=superusuario)
    resposta = getattr(com_permissao, metodo)(_url(rota, metodo), dados)
    assert resposta.status_code == 405

    assert not TipoDocumentoAdministrativo.objects.exists()


ROTAS_COM_TELA_RESTRITA = [
    "/api/parlamentares/dependente/",
    "/api/parlamentares/votante/",
]


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-032")
@pytest.mark.parametrize("rota", ROTAS_COM_TELA_RESTRITA)
def test_rota_de_model_com_tela_restrita_exige_permissao_de_leitura(
    rota, usuario_sem_permissao, superusuario
):
    assert APIClient().get(rota).status_code == 401
    assert APIClient().get(f"{rota}1/").status_code == 401

    sem_permissao = APIClient()
    sem_permissao.force_authenticate(user=usuario_sem_permissao)
    assert sem_permissao.get(rota).status_code == 403

    com_permissao = APIClient()
    com_permissao.force_authenticate(user=superusuario)
    assert com_permissao.get(rota).status_code == 200


ROTAS_DE_TEXTO_ARTICULADO = [
    "/api/compilacao/textoarticulado/",
    "/api/compilacao/dispositivo/",
    "/api/compilacao/publicacao/",
    "/api/compilacao/vide/",
    "/api/compilacao/nota/",
]


@pytest.fixture
def texto_em_edicao_com_conteudo():
    agora = timezone.now()
    texto = baker.make(TextoArticulado, privacidade=STATUS_TA_EDITION)
    dispositivo = baker.make(Dispositivo, ta=texto, ta_publicado=None)
    baker.make(Publicacao, ta=texto)
    baker.make(Vide, dispositivo_base=dispositivo, dispositivo_ref=dispositivo)
    baker.make(
        Nota,
        dispositivo=dispositivo,
        publicidade=NPUBL,
        publicacao=agora,
        efetividade=agora,
    )
    return texto


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-034", "API-ACS-035")
@pytest.mark.parametrize("rota", ROTAS_DE_TEXTO_ARTICULADO)
def test_rotas_de_texto_articulado_seguem_a_visibilidade_do_texto(
    rota, texto_em_edicao_com_conteudo, usuario_sem_permissao, superusuario
):
    sem_permissao = APIClient()
    sem_permissao.force_authenticate(user=usuario_sem_permissao)
    for client in (APIClient(), sem_permissao):
        resposta = client.get(rota)
        assert resposta.status_code == 200
        assert resposta.json()["results"] == []

    com_permissao = APIClient()
    com_permissao.force_authenticate(user=superusuario)
    assert len(com_permissao.get(rota).json()["results"]) == 1


ROTAS_DE_REGISTRO_PESSOAL = [
    "/api/search/chatsession/",
    "/api/search/chatmessage/",
    "/api/arq/draft/",
    "/api/arq/draftmidia/",
]


@pytest.fixture
def dois_usuarios_com_registros(django_user_model):
    """Dois superusuários: passam em qualquer permissão de model, e ainda assim
    cada um só alcança os próprios registros."""
    feitos = {}
    for nome in ("ana", "bia"):
        user = django_user_model.objects.create_superuser(
            email=f"{nome}@exemplo.invalid", password="senha-de-teste-123"
        )
        sessao = baker.make(ChatSession, user=user, session_id=f"sessao-{nome}")
        draft = baker.make(Draft, owner=user, descricao=f"Draft de {nome}")
        client = APIClient()
        client.force_authenticate(user=user)
        feitos[nome] = {
            "client": client,
            "/api/search/chatsession/": sessao,
            "/api/search/chatmessage/": baker.make(
                ChatMessage, chat=sessao, role="user"
            ),
            "/api/arq/draft/": draft,
            "/api/arq/draftmidia/": baker.make(DraftMidia, draft=draft),
        }
    return feitos


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-036", "API-ACS-037")
@pytest.mark.parametrize("rota", ROTAS_DE_REGISTRO_PESSOAL)
def test_rotas_de_registro_pessoal_so_alcancam_os_do_usuario(
    rota, dois_usuarios_com_registros
):
    ana, bia = (dois_usuarios_com_registros[n] for n in ("ana", "bia"))

    assert APIClient().get(rota).status_code == 401

    itens = ana["client"].get(rota).json()["results"]
    assert [item["id"] for item in itens] == [ana[rota].id]

    assert ana["client"].get(f"{rota}{ana[rota].id}/").status_code == 200
    assert ana["client"].get(f"{rota}{bia[rota].id}/").status_code == 404
    assert ana["client"].delete(f"{rota}{bia[rota].id}/").status_code == 404
    assert type(bia[rota]).objects.filter(pk=bia[rota].pk).exists()


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-036")
def test_mensagem_so_e_gravada_em_sessao_do_usuario(dois_usuarios_com_registros):
    ana, bia = (dois_usuarios_com_registros[n] for n in ("ana", "bia"))
    rota = "/api/search/chatmessage/"
    dados = {"role": "user", "content": "texto", "metadata": {}}

    alheia = {**dados, "chat": bia["/api/search/chatsession/"].id}
    assert ana["client"].post(rota, alheia, format="json").status_code == 403
    mover = {"chat": bia["/api/search/chatsession/"].id}
    resposta = ana["client"].patch(f"{rota}{ana[rota].id}/", mover, format="json")
    assert resposta.status_code == 403
    assert ChatMessage.objects.count() == 2

    propria = {**dados, "chat": ana["/api/search/chatsession/"].id}
    assert ana["client"].post(rota, propria, format="json").status_code == 201


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-037")
def test_midia_so_e_gravada_em_draft_do_usuario(dois_usuarios_com_registros):
    ana, bia = (dois_usuarios_com_registros[n] for n in ("ana", "bia"))
    rota = "/api/arq/draftmidia/"
    midia = ana[rota]

    mover = {"draft": bia["/api/arq/draft/"].id}
    resposta = ana["client"].patch(f"{rota}{midia.id}/", mover, format="json")
    assert resposta.status_code == 403
    midia.refresh_from_db()
    assert midia.draft_id == ana["/api/arq/draft/"].id

    manter = {"draft": ana["/api/arq/draft/"].id}
    resposta = ana["client"].patch(f"{rota}{midia.id}/", manter, format="json")
    assert resposta.status_code == 200


ROTAS_DE_CORE_FORA_DA_API = ["user", "auditlog"]


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-039", "API-ACS-041")
def test_app_core_e_registrado_sem_usuario_e_sem_auditoria():
    # resolver uma rota carrega o urlconf, que importa os módulos da API
    assert reverse("sapl.api:core_areatrabalho-list") == "/api/core/areatrabalho/"
    for rota in ROTAS_DE_CORE_FORA_DA_API:
        with pytest.raises(NoReverseMatch):
            reverse(f"sapl.api:core_{rota}-list")

    registrados = ApiViewSetConstrutor._built_sets[AreaTrabalho._meta.app_config]
    assert AreaTrabalho in registrados
    assert get_user_model() not in registrados
    assert AuditLog not in registrados


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-039", "API-ACS-041")
@pytest.mark.parametrize("rota", ROTAS_DE_CORE_FORA_DA_API)
@pytest.mark.parametrize("metodo", ["get"] + METODOS_DE_ESCRITA)
def test_usuario_e_auditoria_nao_tem_rota_na_api(rota, metodo, superusuario):
    cliente = APIClient()
    cliente.force_authenticate(user=superusuario)

    assert cliente.get("/api/core/areatrabalho/").status_code == 200
    assert getattr(cliente, metodo)(f"/api/core/{rota}/").status_code == 404
    assert getattr(cliente, metodo)(f"/api/core/{rota}/1/").status_code == 404


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-043")
@pytest.mark.parametrize(
    "visibilidade",
    [
        DocumentoAdministrativo.STATUS_DOC_ADM_PRIVADO,
        DocumentoAdministrativo.STATUS_DOC_ADM_PUBLICO,
    ],
)
def test_documento_da_area_publica_e_publico_qualquer_que_seja_a_marca(visibilidade):
    def documento(tipo_da_area, numero):
        area = baker.make(AreaTrabalho, tipo=tipo_da_area)
        return baker.make(
            DocumentoAdministrativo,
            tipo=baker.make(TipoDocumentoAdministrativo, workspace=area),
            workspace=area,
            numero=numero,
            ano=2026,
            visibilidade=visibilidade,
        )

    publico = documento(AreaTrabalho.TIPO_PUBLICO, numero=1)
    restrito = documento(AreaTrabalho.TIPO_INSTITUCIONAL, numero=2)
    rota = "/api/protocoloadm/documentoadministrativo/"

    lista = APIClient().get(rota).json()["results"]
    assert [item["id"] for item in lista] == [publico.pk]
    assert APIClient().get(f"{rota}{publico.pk}/").status_code == 200
    assert APIClient().get(f"{rota}{restrito.pk}/").status_code == 404


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-010")
def test_contenttypes_e_publico_e_so_de_leitura(superusuario):
    client = APIClient()

    lista = client.get("/api/contenttypes/contenttype/")

    assert lista.status_code == 200
    registro = lista.json()["results"][0]
    assert {"id", "app_label", "model"} <= set(registro)

    detalhe = f"/api/contenttypes/contenttype/{registro['id']}/"
    assert client.get(detalhe).status_code == 200

    client.force_authenticate(superusuario)
    assert client.post("/api/contenttypes/contenttype/", {}).status_code == 405
    for metodo in (client.put, client.patch, client.delete):
        assert metodo(detalhe, {}).status_code == 405


ROTAS_DE_AREA_DE_TRABALHO = [
    "/api/agenda/evento/",
    "/api/protocoloadm/statustramitacaoadministrativo/",
]


def _registro_da_area(rota, area):
    if "evento" in rota:
        return baker.make(Evento, workspace=area, titulo="Evento", descricao="x")
    return baker.make(
        StatusTramitacaoAdministrativo, workspace=area, sigla="ST", indicador="F"
    )


def _dados_de_registro(rota, registro, area):
    if "evento" in rota:
        return {
            "inicio": "2026-11-22T10:00:00-03:00",
            "titulo": "Outro evento",
            "descricao": "x",
            "tipo": registro.tipo_id,
            "workspace": area.pk,
        }
    return {
        "sigla": "OUT",
        "descricao": "Outro status",
        "indicador": "F",
        "workspace": area.pk,
    }


@pytest.fixture
def operador_de_uma_area(superusuario):
    """Superusuário que opera uma de duas áreas: a regra da área vale também
    para ele."""
    minha = baker.make(AreaTrabalho, tipo=AreaTrabalho.TIPO_INSTITUCIONAL)
    alheia = baker.make(AreaTrabalho, tipo=AreaTrabalho.TIPO_PROCURADORIA)
    baker.make(OperadorAreaTrabalho, user=superusuario, areatrabalho=minha)
    client = APIClient()
    client.force_authenticate(user=superusuario)
    return client, minha, alheia


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-044")
@pytest.mark.parametrize("rota", ROTAS_DE_AREA_DE_TRABALHO)
def test_rota_de_area_de_trabalho_so_alcanca_os_registros_da_area_do_operador(
    rota, operador_de_uma_area, superusuario
):
    client, minha, alheia = operador_de_uma_area
    meu = _registro_da_area(rota, minha)
    alheio = _registro_da_area(rota, alheia)

    assert APIClient().get(rota).status_code == 401

    lista = client.get(rota).json()["results"]
    assert [r["id"] for r in lista] == [meu.pk]
    assert client.get(f"{rota}{meu.pk}/").status_code == 200
    assert client.get(f"{rota}{alheio.pk}/").status_code == 404

    assert client.patch(f"{rota}{alheio.pk}/", {"descricao": "y"}).status_code == 404
    assert client.delete(f"{rota}{alheio.pk}/").status_code == 404
    assert type(alheio).objects.filter(pk=alheio.pk).exists()

    superusuario.operadorareatrabalho_set.all().delete()
    assert client.get(rota).json()["results"] == []


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-044")
@pytest.mark.parametrize("rota", ROTAS_DE_AREA_DE_TRABALHO)
def test_rota_de_area_de_trabalho_so_grava_na_area_do_operador(
    rota, operador_de_uma_area
):
    client, minha, alheia = operador_de_uma_area
    meu = _registro_da_area(rota, minha)
    model = type(meu)

    na_alheia = _dados_de_registro(rota, meu, alheia)
    assert client.post(rota, na_alheia).status_code == 403
    mover = client.patch(f"{rota}{meu.pk}/", {"workspace": alheia.pk})
    assert mover.status_code == 403
    assert list(model.objects.values_list("workspace", flat=True)) == [minha.pk]

    assert client.patch(f"{rota}{meu.pk}/", {"descricao": "nova"}).status_code == 200
    na_minha = _dados_de_registro(rota, meu, minha)
    assert client.post(rota, na_minha).status_code == 201
    assert model.objects.filter(workspace=minha).count() == 2


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-045")
@pytest.mark.parametrize("action", ["despesas_agrupadas", "espelho"])
def test_consulta_de_despesa_de_loa_nao_publicada_exige_autenticacao(action):
    nao_publicada = baker.make(Loa, ano=2090, publicado=False)
    publicada = baker.make(Loa, ano=2091, publicado=True)
    dados = {"agrupamento": "orgao", "itens": 5, "hist": 0}

    resposta = APIClient().post(
        f"/api/loa/loa/{nao_publicada.pk}/{action}/", dados, format="json"
    )
    assert resposta.status_code == 401

    resposta = APIClient().post(
        f"/api/loa/loa/{publicada.pk}/{action}/", dados, format="json"
    )
    assert resposta.status_code == 200


@pytest.fixture
def tipos_de_proposicao_por_tipo_de_autor(django_user_model):
    """Um tipo de proposição para parlamentar e outro para comissão, e um
    operador de um autor que é parlamentar."""
    tipo_de_materia = baker.make(TipoMateriaLegislativa, sigla="PL", descricao="Lei")
    conteudo = ContentType.objects.get_for_model(TipoMateriaLegislativa)

    def tipo_de_autor(model):
        return TipoAutor.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(model),
            defaults={"descricao": model._meta.verbose_name},
        )[0]

    def tipo_de_proposicao(descricao, para):
        tipo = baker.make(
            TipoProposicao,
            descricao=descricao,
            content_type=conteudo,
            object_id=tipo_de_materia.pk,
        )
        tipo.tipo_autores.set([para])
        return tipo

    de_parlamentar = tipo_de_autor(Parlamentar)
    tipo_de_proposicao("Projeto de parlamentar", de_parlamentar)
    tipo_de_proposicao("Parecer de comissão", tipo_de_autor(Comissao))

    operador = django_user_model.objects.create_user(
        email="operador-de-autor@exemplo.invalid", password="senha-de-teste-123"
    )
    autor = baker.make(Autor, tipo=de_parlamentar, nome="Autor parlamentar")
    baker.make(OperadorAutor, user=operador, autor=autor)
    return operador


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-049")
def test_tipos_de_proposicao_do_autor_conectado(
    tipos_de_proposicao_por_tipo_de_autor, usuario_sem_permissao
):
    rota = "/api/materia/tipoproposicao/tipos_do_autor_contectado/"

    assert APIClient().get(rota).status_code == 401

    sem_autor = APIClient()
    sem_autor.force_authenticate(user=usuario_sem_permissao)
    resposta = sem_autor.get(rota)
    assert resposta.status_code == 200
    assert resposta.json()["results"] == []

    operador = APIClient()
    operador.force_authenticate(user=tipos_de_proposicao_por_tipo_de_autor)
    resposta = operador.get(rota)
    assert resposta.status_code == 200
    assert [t["descricao"] for t in resposta.json()["results"]] == [
        "Projeto de parlamentar"
    ]


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-050")
def test_requisicao_anonima_com_parametro_u_e_recusada_antes_da_view(
    client, usuario_sem_permissao
):
    rota = "/api/materia/tipomaterialegislativa/"
    viewset = ApiViewSetConstrutor.get_viewset_for_model(TipoMateriaLegislativa)

    with mock.patch.object(viewset, "list") as lista:
        resposta = client.get(rota, {"u": "1795380000"})

    assert resposta.status_code == 444
    assert resposta.content == b""
    assert not lista.called

    assert client.get(rota).status_code == 200

    # quem está autenticado por sessão é atendido
    client.force_login(usuario_sem_permissao)
    assert client.get(rota, {"u": "1795380000"}).status_code == 200
