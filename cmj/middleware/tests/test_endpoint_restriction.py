import pytest
from django.http import HttpResponse
from django.test import Client, RequestFactory

from cmj.middleware.endpoint_restriction import EndpointRestrictionMiddleware

pytestmark = pytest.mark.django_db


@pytest.fixture
def middleware():
    return EndpointRestrictionMiddleware(lambda request: HttpResponse("ok"))


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.spec("INFRA-OPS-001")
@pytest.mark.parametrize(
    "path",
    ["/metrics", "/health/", "/ready/", "/version/", "/health", "/ready", "/version"],
)
def test_ip_publico_em_x_real_ip_e_negado(middleware, rf, path):
    request = rf.get(path, HTTP_X_REAL_IP="200.150.10.20", REMOTE_ADDR="172.18.0.1")
    assert middleware(request).status_code == 403


@pytest.mark.spec("INFRA-OPS-002")
@pytest.mark.parametrize("xff", ["127.0.0.1", "10.0.0.5", "127.0.0.1, 200.150.10.20"])
def test_decisao_ignora_x_forwarded_for(middleware, rf, xff):
    request = rf.get(
        "/metrics",
        HTTP_X_FORWARDED_FOR=xff,
        HTTP_X_REAL_IP="200.150.10.20",
        REMOTE_ADDR="172.18.0.1",
    )
    assert middleware(request).status_code == 403


@pytest.mark.spec("INFRA-OPS-001")
@pytest.mark.parametrize("ip", ["127.0.0.1", "172.18.0.5", "10.1.2.3", "192.168.0.10"])
def test_ip_privado_em_x_real_ip_passa(middleware, rf, ip):
    request = rf.get("/metrics", HTTP_X_REAL_IP=ip)
    assert middleware(request).status_code == 200


@pytest.mark.spec("INFRA-OPS-001")
def test_sem_x_real_ip_usa_remote_addr(middleware, rf):
    assert middleware(rf.get("/metrics", REMOTE_ADDR="172.18.0.5")).status_code == 200
    assert (
        middleware(rf.get("/metrics", REMOTE_ADDR="200.150.10.20")).status_code == 403
    )


@pytest.mark.spec("INFRA-OPS-003")
def test_ip_invalido_e_negado(middleware, rf):
    request = rf.get("/metrics", HTTP_X_REAL_IP="nao-e-ip")
    assert middleware(request).status_code == 403


@pytest.mark.spec("INFRA-OPS-004")
@pytest.mark.parametrize("path", ["/", "/metrics/", "/api/materia/materialegislativa/"])
def test_caminho_fora_da_lista_nao_e_afetado(middleware, rf, path):
    request = rf.get(path, HTTP_X_REAL_IP="200.150.10.20")
    assert middleware(request).status_code == 200


@pytest.mark.spec("INFRA-OPS-006")
@pytest.mark.parametrize("path", ["/metrics", "/health/", "/ready/", "/version/"])
def test_rotas_reais_negadas_para_ip_publico(path):
    resposta = Client().get(path, HTTP_X_REAL_IP="200.150.10.20")
    assert resposta.status_code == 403


@pytest.mark.spec("INFRA-OPS-007")
@pytest.mark.parametrize("path", ["/health/", "/version/", "/version/?fmt=txt"])
def test_rotas_de_saude_e_versao_respondem_para_rede_privada(path, settings):
    resposta = Client().get(path, HTTP_X_REAL_IP="172.18.0.5")
    assert resposta.status_code == 200
    if "fmt" not in path:
        assert resposta.json()["version"] == settings.PORTALCMJ_VERSION


@pytest.mark.spec("INFRA-OPS-008")
@pytest.mark.parametrize(
    "ip", ["192.0.2.10", "2001:db8::1", "224.0.0.1", "ff02::1", "fe80::1", "127.0.0.11"]
)
def test_so_loopback_e_redes_privadas_sao_aceitos(middleware, rf, ip):
    request = rf.get("/metrics", HTTP_X_REAL_IP=ip)
    assert middleware(request).status_code == 403


@pytest.mark.spec("INFRA-OPS-008")
def test_rede_privada_ipv6_e_aceita(middleware, rf):
    request = rf.get("/metrics", HTTP_X_REAL_IP="fd00::5")
    assert middleware(request).status_code == 200
