"""Geração dos viewsets pelo drfautoapi (docs/specs/api/gerador.md)."""

import sys
import types
from datetime import timedelta
from importlib.machinery import ModuleSpec

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from model_bakery import baker
from rest_framework import serializers
from rest_framework.test import APIClient

import sapl.api.urls  # noqa: F401  carrega os viewsets, como o URLconf faz
from cmj.loa.models import Orgao as OrgaoDaLoa
from drfautoapi.drfautoapi import ApiFilterSetMixin, ApiViewSetConstrutor
from sapl.base.models import Autor, TipoAutor
from sapl.materia.models import Orgao as OrgaoDaMateria
from sapl.materia.models import Proposicao
from sapl.parlamentares.models import Parlamentar

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def registro(monkeypatch):
    """Uma cópia do registro de viewsets: o que o teste gerar não fica."""
    copia = {
        app: dict(models) for app, models in ApiViewSetConstrutor._built_sets.items()
    }
    monkeypatch.setattr(ApiViewSetConstrutor, "_built_sets", copia)
    return copia


@pytest.fixture
def modulo(monkeypatch):
    """Cria um módulo importável com as classes dadas."""

    def criar(nome, importando=False, **classes):
        module = types.ModuleType(nome)
        module.__spec__ = ModuleSpec(nome, None)
        module.__spec__._initializing = importando
        for nome_da_classe, classe in classes.items():
            setattr(module, nome_da_classe, classe)
        monkeypatch.setitem(sys.modules, nome, module)
        return nome

    return criar


def _viewset_gerado(registro, model):
    return registro[model._meta.app_config][model]


@pytest.mark.spec("API-GER-040")
@pytest.mark.parametrize(
    "configuracao",
    [
        {"SERIALIZER_MODULE": ["modulo.que.nao.existe"]},
        {"FILTER_MODULE": "cmj.api.forms,modulo.que.nao.existe"},
        {"SERIALIZER_MIXIN": "modulo.que.nao.existe.Mixin"},
        {"FILTERSET_MIXIN": "cmj.api.forms.ClasseQueNaoExiste"},
    ],
)
def test_modulo_ou_mixin_configurado_que_nao_importa_interrompe_a_geracao(
    registro, configuracao
):
    antes = _viewset_gerado(registro, OrgaoDaMateria)

    with pytest.raises(ImproperlyConfigured, match="drfautoapi"):
        ApiViewSetConstrutor.build_class([OrgaoDaMateria], **configuracao)

    assert _viewset_gerado(registro, OrgaoDaMateria) is antes


@pytest.mark.spec("API-GER-040")
@pytest.mark.parametrize("parametro", ["SERIALIZER_MODULE", "FILTER_MODULE"])
def test_modulo_configurado_ainda_em_importacao_interrompe_a_geracao(
    registro, modulo, parametro
):
    nome = modulo("modulo_pela_metade", importando=True)

    with pytest.raises(ImproperlyConfigured, match="ainda está sendo importado"):
        ApiViewSetConstrutor.build_class([OrgaoDaMateria], **{parametro: [nome]})


@pytest.mark.spec("API-GER-040")
def test_modulo_configurado_que_importa_entrega_as_classes_proprias(registro, modulo):
    class OrgaoSerializer(serializers.ModelSerializer):
        class Meta:
            model = OrgaoDaMateria
            fields = "__all__"

    class OrgaoFilterSet(ApiFilterSetMixin):
        pass

    ApiViewSetConstrutor.build_class(
        [OrgaoDaMateria],
        SERIALIZER_MODULE=[
            modulo("serializers_de_teste", OrgaoSerializer=OrgaoSerializer)
        ],
        FILTER_MODULE=[modulo("filtersets_de_teste", OrgaoFilterSet=OrgaoFilterSet)],
    )

    viewset = _viewset_gerado(registro, OrgaoDaMateria)
    assert issubclass(viewset.serializer_class, OrgaoSerializer)
    assert issubclass(viewset.filterset_class, OrgaoFilterSet)


@pytest.mark.spec("API-GER-041")
@pytest.mark.parametrize("parametro", ["SERIALIZER_MODULE", "FILTER_MODULE"])
def test_classe_achada_pelo_nome_para_model_de_outro_app_interrompe_a_geracao(
    registro, modulo, parametro
):
    class Meta:
        model = OrgaoDaLoa
        fields = "__all__"

    base = (
        serializers.ModelSerializer
        if parametro == "SERIALIZER_MODULE"
        else ApiFilterSetMixin
    )
    sufixo = "Serializer" if parametro == "SERIALIZER_MODULE" else "FilterSet"
    classe = type(f"Orgao{sufixo}", (base,), {"Meta": Meta})
    nome = modulo("classes_de_outro_app", **{f"Orgao{sufixo}": classe})
    antes = _viewset_gerado(registro, OrgaoDaMateria)

    with pytest.raises(ImproperlyConfigured, match="loa.Orgao.*materia.Orgao"):
        ApiViewSetConstrutor.build_class([OrgaoDaMateria], **{parametro: [nome]})

    assert _viewset_gerado(registro, OrgaoDaMateria) is antes

    # para o model que ela declara, a mesma classe vale
    ApiViewSetConstrutor.build_class([OrgaoDaLoa], **{parametro: [nome]})
    atributo = (
        "serializer_class" if parametro == "SERIALIZER_MODULE" else "filterset_class"
    )
    assert issubclass(getattr(_viewset_gerado(registro, OrgaoDaLoa), atributo), classe)


@pytest.mark.spec("API-GER-041")
def test_nenhuma_classe_propria_em_uso_declara_model_de_outro_app():
    for models in ApiViewSetConstrutor._built_sets.values():
        for model, viewset in models.items():
            for classe in (viewset.serializer_class, viewset.filterset_class):
                declarado = getattr(getattr(classe, "Meta", None), "model", None)
                assert declarado in (None, model), (classe, model)


@pytest.fixture
def parlamentar_com_proposicoes():
    """Um parlamentar com uma proposição recebida e outras que a tela de
    proposições do parlamentar não lista."""
    tipo_de_conteudo = ContentType.objects.get_for_model(Parlamentar)
    tipo, _criado = TipoAutor.objects.get_or_create(
        content_type=tipo_de_conteudo, defaults={"descricao": "Parlamentar"}
    )
    ontem = timezone.now() - timedelta(days=1)

    def autor_de(parlamentar):
        return baker.make(
            Autor,
            tipo=tipo,
            content_type=tipo_de_conteudo,
            object_id=parlamentar.pk,
            nome=parlamentar.nome_parlamentar,
        )

    parlamentar = baker.make(Parlamentar, nome_parlamentar="Ana", cpf="111.111.111-11")
    autor = autor_de(parlamentar)
    outro = autor_de(baker.make(Parlamentar, nome_parlamentar="Bia"))

    def proposicao(descricao, **campos):
        dados = {
            "autor": autor,
            "data_envio": ontem,
            "data_recebimento": ontem,
            "cancelado": False,
        }
        dados.update(campos)
        return baker.make(Proposicao, descricao=descricao, **dados)

    proposicao("Recebida")
    proposicao("Em elaboração", data_envio=None, data_recebimento=None)
    proposicao("Enviada e não recebida", data_recebimento=None)
    proposicao("Cancelada", cancelado=True)
    proposicao("De outro parlamentar", autor=outro)
    return parlamentar


@pytest.mark.spec("API-GER-042")
@pytest.mark.parametrize("autenticado", [False, True], ids=["anonimo", "sem_permissao"])
def test_proposicoes_do_parlamentar_respondem_a_todos_como_a_tela(
    parlamentar_com_proposicoes, django_user_model, autenticado
):
    client = APIClient()
    if autenticado:
        client.force_authenticate(
            django_user_model.objects.create_user(
                email="sem-permissao@exemplo.invalid", password="senha-de-teste-123"
            )
        )

    resposta = client.get(
        f"/api/parlamentares/parlamentar/{parlamentar_com_proposicoes.pk}/proposicoes/"
    )

    assert resposta.status_code == 200
    assert [p["descricao"] for p in resposta.json()["results"]] == ["Recebida"]


@pytest.mark.spec("API-GER-042")
def test_lista_de_parlamentares_continua_sem_os_campos_pessoais(
    parlamentar_com_proposicoes,
):
    resposta = APIClient().get("/api/parlamentares/parlamentar/")

    assert resposta.status_code == 200
    item = resposta.json()["results"][0]
    assert "nome_parlamentar" in item
    assert "cpf" not in item


@pytest.mark.spec("API-GER-043")
def test_cada_rota_da_api_e_registrada_uma_vez_so():
    padroes = [(str(p.pattern), p.name) for p in sapl.api.urls.urlpatterns_router]

    assert len(padroes) == len(set(padroes))
    nomes = {nome for _padrao, nome in padroes}
    assert {"documento-list", "materia_materialegislativa-list", "api-root"} <= nomes


@pytest.mark.spec("API-GER-043")
def test_raiz_da_api_lista_as_rotas_geradas_e_a_de_documento():
    rotas = APIClient().get("/api/").json()

    assert "documento" in rotas
    assert "materia/materialegislativa" in rotas
    geradas = sum(len(m) for m in ApiViewSetConstrutor._built_sets.values())
    assert len(rotas) == geradas + 1
