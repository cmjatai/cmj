"""Paginação e ``get_all`` nas rotas geradas (docs/specs/api/paginacao-custo.md)."""

import pytest
from django.contrib.auth.models import Permission
from model_bakery import baker
from rest_framework.test import APIClient

from sapl.parlamentares.models import NivelInstrucao

ROTA = "/api/parlamentares/nivelinstrucao/"
TETO = 2


@pytest.fixture(autouse=True)
def teto_baixo(settings):
    settings.API_GET_ALL_MAX_ITEMS = TETO


def _niveis(quantidade):
    return [
        baker.make(NivelInstrucao, descricao=f"Nível {n}") for n in range(quantidade)
    ]


def _autenticado(django_user_model, nome, permissao=None, **kwargs):
    user = django_user_model.objects.create_user(
        email=f"{nome}@exemplo.invalid", password="senha-de-teste-123", **kwargs
    )
    if permissao:
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="parlamentares", codename=permissao
            )
        )
    client = APIClient()
    client.force_authenticate(user=django_user_model.objects.get(pk=user.pk))
    return client


@pytest.mark.django_db
@pytest.mark.spec("API-CUS-020")
def test_get_all_devolve_a_lista_inteira_ate_o_teto():
    _niveis(TETO)

    resposta = APIClient().get(ROTA, {"get_all": "true"})

    assert resposta.status_code == 200
    assert len(resposta.json()) == TETO


@pytest.mark.django_db
@pytest.mark.spec("API-CUS-020")
def test_get_all_acima_do_teto_pede_paginacao_a_quem_nao_tem_permissao_de_leitura(
    django_user_model,
):
    _niveis(TETO + 1)
    sem_permissao = _autenticado(django_user_model, "sem-permissao")

    for client in (APIClient(), sem_permissao):
        resposta = client.get(ROTA, {"get_all": "true"})
        assert resposta.status_code == 400
        assert "get_all" in resposta.json()

        # com filtro que traz o resultado para dentro do teto, a lista sai
        filtrada = client.get(ROTA, {"get_all": "true", "descricao": "Nível 0"})
        assert filtrada.status_code == 200
        assert len(filtrada.json()) == 1

        # a paginação não tem teto de itens na tabela
        paginada = client.get(ROTA)
        assert paginada.status_code == 200
        assert paginada.json()["pagination"]["total_entries"] == TETO + 1


@pytest.mark.django_db
@pytest.mark.spec("API-CUS-020")
def test_get_all_nao_tem_teto_para_quem_tem_a_permissao_de_leitura_do_model(
    django_user_model,
):
    _niveis(TETO + 1)
    com_permissao = _autenticado(
        django_user_model, "com-permissao", "list_nivelinstrucao"
    )

    resposta = com_permissao.get(ROTA, {"get_all": "true"})

    assert resposta.status_code == 200
    assert len(resposta.json()) == TETO + 1
