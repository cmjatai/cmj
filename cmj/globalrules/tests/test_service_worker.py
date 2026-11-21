"""Testes da view do service worker (docs/specs/v2018/estrutura.md)."""

from unittest import mock

import pytest
from django.test import RequestFactory, override_settings

from cmj.globalrules import views

pytestmark = [pytest.mark.django_db, pytest.mark.spec("V2018-EST-044")]


def _url_consultada(caminho, host):
    resposta = mock.Mock(status_code=200, content=b"/* sw */")
    with mock.patch.object(views.requests, "get", return_value=resposta) as get:
        request = RequestFactory().get(caminho, HTTP_HOST=host)
        response = views.service_worker_proxy(request)
    assert response.status_code == 200
    assert response.content == b"/* sw */"
    return get.call_args.args[0]


@pytest.mark.parametrize(
    "caminho, url",
    [
        ("/service-worker.js", "http://dev.interno:8080/service-worker.js"),
        ("/v6/service-worker.js", "http://dev.interno:5173/static/service-worker.js"),
        ("/v8/service-worker.js", "http://dev.interno:5174/static/service-worker.js"),
    ],
)
def test_em_debug_consulta_o_dev_server_configurado(caminho, url):
    with override_settings(DEBUG=True, DEV_HOST_NAME="dev.interno"):
        assert _url_consultada(caminho, "outro.exemplo:9098") == url
        assert _url_consultada(caminho, "outro.exemplo") == url


@pytest.mark.parametrize(
    "caminho, url",
    [
        ("/service-worker.js", "http://cmjfront2018:8080/service-worker.js"),
        ("/v6/service-worker.js", "http://cmjfront2026:5173/static/service-worker.js"),
        ("/v8/service-worker.js", "http://cmjfrontv8:5174/static/service-worker.js"),
    ],
)
def test_em_debug_no_container_consulta_o_container_do_frontend(caminho, url):
    with override_settings(DEBUG=True, DEV_HOST_NAME="dev.interno"):
        assert _url_consultada(caminho, "outro.exemplo:9099") == url


def test_sem_debug_nao_consulta_dev_server():
    with override_settings(DEBUG=False):
        with mock.patch.object(views.requests, "get") as get:
            request = RequestFactory().get("/service-worker.js", HTTP_HOST="a:9099")
            response = views.service_worker_proxy(request)
    assert not get.called
    assert response["Service-Worker-Allowed"] == "/"
