"""Filtros e ordenação gerados nas rotas da API (docs/specs/api/filtros.md)."""

import pytest
from django.http import QueryDict
from model_bakery import baker
from rest_framework.test import APIClient

from drfautoapi.drfautoapi import ApiViewSetConstrutor
from sapl.parlamentares.models import Filiacao, Parlamentar, Partido

URL_PARLAMENTAR = "/api/parlamentares/parlamentar/"
URL_FILIACAO = "/api/parlamentares/filiacao/"


@pytest.fixture
def filiacoes():
    """Duas filiações em que a ordem por parlamentar, por partido e por CPF do
    parlamentar são diferentes entre si."""
    ana = baker.make(
        Parlamentar, nome_completo="Ana", nome_parlamentar="Ana", cpf="999.999.999-99"
    )
    bia = baker.make(
        Parlamentar, nome_completo="Bia", nome_parlamentar="Bia", cpf="111.111.111-11"
    )
    return [
        baker.make(Filiacao, parlamentar=ana, partido=baker.make(Partido, sigla="ZZ")),
        baker.make(Filiacao, parlamentar=bia, partido=baker.make(Partido, sigla="AA")),
    ]


@pytest.fixture
def anonimo():
    return APIClient()


@pytest.fixture
def superusuario(django_user_model):
    client = APIClient()
    client.force_authenticate(
        user=django_user_model.objects.create_superuser(
            email="superusuario@exemplo.invalid", password="senha-de-teste-123"
        )
    )
    return client


def _nomes(client, params):
    resposta = client.get(URL_PARLAMENTAR, params)
    assert resposta.status_code == 200
    return [item["nome_parlamentar"] for item in resposta.json()["results"]]


def _parlamentares_das_filiacoes(client, params):
    resposta = client.get(URL_FILIACAO, params)
    assert resposta.status_code == 200
    return [item["parlamentar"] for item in resposta.json()["results"]]


@pytest.mark.django_db
@pytest.mark.spec("API-FIL-020")
@pytest.mark.parametrize(
    "filtro",
    [
        {"cpf": "111.111.111-11"},
        {"cpf__startswith": "1"},
        {"cpf__endswith": "-11"},
        {"cpf__gt": "5"},
    ],
)
def test_filtro_gerado_vale_so_para_campo_que_o_usuario_recebe(
    anonimo, superusuario, filiacoes, filtro
):
    # quem não recebe o campo tem o filtro ignorado, como parâmetro desconhecido
    assert _nomes(anonimo, filtro) == ["Ana", "Bia"]

    # quem recebe o campo filtra por ele
    assert len(_nomes(superusuario, filtro)) == 1


@pytest.mark.django_db
@pytest.mark.spec("API-FIL-020")
def test_filtro_por_campo_recebido_independe_de_include_e_exclude(anonimo, filiacoes):
    filtro = {"nome_parlamentar": "Bia"}

    assert _nomes(anonimo, filtro) == ["Bia"]

    for controle in ({"include": "id"}, {"exclude": "nome_parlamentar"}):
        resposta = anonimo.get(URL_PARLAMENTAR, {**filtro, **controle})
        assert resposta.json()["pagination"]["total_entries"] == 1


@pytest.mark.django_db
@pytest.mark.spec("API-FIL-021")
def test_ordenacao_vale_so_para_campo_que_o_usuario_recebe(
    anonimo, superusuario, filiacoes
):
    # sem o campo, a ordenação é ignorada e vale a ordem padrão do model
    assert _nomes(anonimo, {"o": "cpf"}) == ["Ana", "Bia"]
    assert _nomes(anonimo, {"o": "-nome_parlamentar,cpf"}) == ["Ana", "Bia"]

    assert _nomes(anonimo, {"o": "-nome_parlamentar"}) == ["Bia", "Ana"]
    assert _nomes(superusuario, {"o": "cpf"}) == ["Bia", "Ana"]


@pytest.mark.django_db
@pytest.mark.spec("API-FIL-021")
def test_ordenacao_atravessa_so_relacao_que_o_usuario_pode_ler(
    anonimo, superusuario, filiacoes
):
    ana, bia = [f.parlamentar_id for f in filiacoes]
    padrao = _parlamentares_das_filiacoes(anonimo, {})
    assert padrao == [ana, bia]

    # parlamentar tem rota de leitura pública; partido, não
    por_parlamentar = {"o": "-parlamentar__nome_parlamentar"}
    assert _parlamentares_das_filiacoes(anonimo, por_parlamentar) == [bia, ana]

    por_partido = {"o": "partido__sigla"}
    assert _parlamentares_das_filiacoes(anonimo, por_partido) == padrao
    assert _parlamentares_das_filiacoes(superusuario, por_partido) == [bia, ana]

    # o campo oculto do model relacionado também não ordena
    por_cpf = {"o": "parlamentar__cpf"}
    assert _parlamentares_das_filiacoes(anonimo, por_cpf) == padrao
    assert _parlamentares_das_filiacoes(superusuario, por_cpf) == [bia, ana]


def _filterset_de_parlamentar():
    return ApiViewSetConstrutor.get_viewset_for_model(Parlamentar).filterset_class


@pytest.mark.django_db
@pytest.mark.spec("API-FIL-026")
def test_so_os_filtros_citados_na_requisicao_sao_instanciados():
    classe = _filterset_de_parlamentar()
    gerados = set(classe.base_filters) - set(classe.declared_filters)
    assert {"nome_parlamentar__icontains", "ativo", "nome_completo"} <= gerados

    citando = classe(
        QueryDict("nome_parlamentar__icontains=a&ativo=true&nao_e_filtro=1"),
        queryset=Parlamentar.objects.all(),
    )
    sem_citar = classe(QueryDict(""), queryset=Parlamentar.objects.all())

    assert set(citando.filters) == set(classe.declared_filters) | {
        "nome_parlamentar__icontains",
        "ativo",
    }
    assert set(sem_citar.filters) == set(classe.declared_filters)
    # a classe continua com todos, de onde o esquema os lê
    assert gerados <= set(classe.base_filters)


@pytest.mark.django_db
@pytest.mark.spec("API-FIL-026")
def test_filtro_citado_filtra_e_valor_invalido_responde_400(anonimo, filiacoes):
    assert _nomes(anonimo, {"nome_parlamentar__icontains": "ana"}) == ["Ana"]
    assert _nomes(anonimo, {}) == ["Ana", "Bia"]

    resposta = anonimo.get(URL_PARLAMENTAR, {"ativo": "talvez"})
    assert resposta.status_code == 400
    assert "ativo" in resposta.json()


@pytest.mark.django_db
@pytest.mark.spec("API-FIL-027")
def test_nenhum_filtro_gerado_usa_expressao_regular():
    for models in ApiViewSetConstrutor._built_sets.values():
        for viewset in models.values():
            com_regex = [
                nome
                for nome in viewset.filterset_class.base_filters
                if {"regex", "iregex"} & set(nome.split("__"))
            ]
            assert com_regex == []


@pytest.mark.django_db
@pytest.mark.spec("API-FIL-027")
@pytest.mark.parametrize("lookup", ["regex", "iregex"])
def test_parametro_de_expressao_regular_e_ignorado(anonimo, filiacoes, lookup):
    resposta = anonimo.get(URL_PARLAMENTAR, {f"nome_parlamentar__{lookup}": "("})

    assert resposta.status_code == 200
    assert len(resposta.json()["results"]) == 2


@pytest.mark.django_db
@pytest.mark.spec("API-FIL-028")
@pytest.mark.parametrize(
    "params",
    [
        {"filtro_que_nao_existe": "1"},
        {"o": "campo_que_nao_existe"},
        {"id__in": "abc"},
    ],
)
def test_parametro_desconhecido_ou_invalido_e_ignorado_em_silencio(
    anonimo, filiacoes, params
):
    resposta = anonimo.get(URL_PARLAMENTAR, params)

    assert resposta.status_code == 200
    assert len(resposta.json()["results"]) == 2
