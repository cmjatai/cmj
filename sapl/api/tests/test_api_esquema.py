"""Esquema OpenAPI da API (docs/specs/api/paginacao-custo.md)."""

from unittest import mock

import pytest
from django.core.cache import cache
from drf_spectacular.settings import spectacular_settings
from rest_framework.test import APIClient

from sapl.api.views_schema import CachedSchemaAPIView

URL = "/api/schema/"
ESQUEMA = {"openapi": "3.0.3", "info": {"title": "Teste", "version": "1"}, "paths": {}}


@pytest.fixture
def cache_em_memoria(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "api-esquema",
        }
    }
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def gerador():
    """Troca a geração do esquema por um esquema mínimo e conta as chamadas."""
    with mock.patch.object(
        CachedSchemaAPIView.generator_class, "get_schema", return_value=ESQUEMA
    ) as get_schema:
        yield get_schema


@pytest.mark.django_db
@pytest.mark.spec("API-CUS-022")
def test_esquema_e_gerado_uma_vez_e_depois_vem_do_cache(cache_em_memoria, gerador):
    client = APIClient()

    primeira = client.get(URL)
    segunda = client.get(URL)

    assert primeira.status_code == segunda.status_code == 200
    assert gerador.call_count == 1
    assert segunda.content == primeira.content
    assert segunda["Content-Type"] == primeira["Content-Type"]
    assert "filename=" in segunda["Content-Disposition"]


@pytest.mark.django_db
@pytest.mark.spec("API-CUS-022")
@pytest.mark.parametrize("parametros", [{"version": "qualquer"}, {"lang": "zz"}])
def test_parametro_que_nao_muda_o_esquema_nao_gera_de_novo(
    cache_em_memoria, gerador, parametros
):
    client = APIClient()

    client.get(URL)
    resposta = client.get(URL, parametros)

    assert resposta.status_code == 200
    assert gerador.call_count == 1
    assert "qualquer" not in resposta["Content-Disposition"]


@pytest.mark.django_db
@pytest.mark.spec("API-CUS-022")
def test_cada_formato_do_esquema_tem_a_sua_copia_no_cache(cache_em_memoria, gerador):
    client = APIClient()

    yaml = client.get(URL)
    json = client.get(URL, {"format": "json"})
    client.get(URL, {"format": "json"})

    assert gerador.call_count == 2
    assert yaml["Content-Type"] != json["Content-Type"]
    assert json.json() == ESQUEMA


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-011")
@pytest.mark.parametrize("url", [URL, "/api/schema/swagger-ui/", "/api/schema/redoc/"])
def test_esquema_e_documentacao_respondem_sem_autenticacao(gerador, url):
    assert APIClient().get(url).status_code == 200


@pytest.mark.django_db
@pytest.mark.spec("API-ACS-011")
def test_esquema_descreve_todas_as_rotas_para_qualquer_usuario():
    # com SERVE_PUBLIC o esquema não é filtrado pelas permissões de quem pede
    assert spectacular_settings.SERVE_PUBLIC is True
