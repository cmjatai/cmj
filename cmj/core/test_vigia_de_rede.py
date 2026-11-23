"""O vigia de rede do conftest barra a comunicação externa nos testes.

Os destinos externos usados aqui são reservados para documentação: o nome
``externo.invalid`` nunca resolve e a faixa 203.0.113.0/24 não é roteada.
"""

import socket
from unittest import mock

import pytest
import requests
from django.conf import settings

IP_EXTERNO = "203.0.113.10"
NOME_EXTERNO = "externo.invalid"


@pytest.fixture
def originais(vigia_de_rede):
    """As funções verdadeiras de socket, trocadas por mock: o teste confere
    que nenhuma foi chamada."""
    mocks = {chave: mock.Mock() for chave in vigia_de_rede._originais}
    with mock.patch.dict(vigia_de_rede._originais, mocks):
        yield mocks


def _nenhuma_chamada(originais):
    return not any(m.called for m in originais.values())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "operacao",
    [
        lambda s: s.connect((IP_EXTERNO, 443)),
        lambda s: s.connect_ex((IP_EXTERNO, 443)),
        lambda s: s.sendto(b"x", (IP_EXTERNO, 53)),
        lambda s: s.sendto(b"x", 0, (IP_EXTERNO, 53)),
        lambda s: s.connect((NOME_EXTERNO, 443)),
        lambda s: socket.getaddrinfo(NOME_EXTERNO, 443),
        lambda s: socket.gethostbyname(NOME_EXTERNO),
        lambda s: socket.gethostbyname_ex(NOME_EXTERNO),
        lambda s: socket.create_connection((NOME_EXTERNO, 443)),
    ],
    ids=[
        "connect",
        "connect_ex",
        "sendto",
        "sendto com flags",
        "connect por nome",
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "create_connection",
    ],
)
def test_destino_externo_e_barrado_antes_de_sair(vigia_de_rede, originais, operacao):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        with pytest.raises(OSError, match="Comunicação externa barrada"):
            operacao(s)

    assert _nenhuma_chamada(originais)
    assert len(vigia_de_rede.tentativas) == 1
    vigia_de_rede.tentativas.clear()


@pytest.mark.django_db
def test_cliente_http_nao_alcanca_destino_externo(vigia_de_rede, originais):
    with pytest.raises(requests.ConnectionError):
        requests.get(f"https://{NOME_EXTERNO}/bot/sendMessage", timeout=1)

    assert _nenhuma_chamada(originais)
    assert vigia_de_rede.tentativas
    vigia_de_rede.tentativas.clear()


@pytest.mark.django_db
def test_tentativa_engolida_pelo_codigo_reprova_o_teste(vigia_de_rede, originais):
    assert vigia_de_rede.reprovacao() is None

    try:
        socket.create_connection((IP_EXTERNO, 443))
    except Exception:
        pass

    assert IP_EXTERNO in vigia_de_rede.reprovacao()
    vigia_de_rede.tentativas.clear()


@pytest.mark.django_db
def test_conexao_local_passa(vigia_de_rede):
    with socket.socket() as servidor:
        servidor.bind(("127.0.0.1", 0))
        servidor.listen(1)
        with socket.create_connection(servidor.getsockname(), timeout=2):
            pass

    assert socket.getaddrinfo("localhost", 80)
    assert vigia_de_rede.tentativas == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "host, local",
    [
        ("127.0.0.1", True),
        ("::1", True),
        ("10.1.2.3", True),
        ("172.18.0.3", True),
        ("192.168.15.9", True),
        ("fe80::1", True),
        ("::ffff:192.168.15.9", True),
        ("8.8.8.8", False),
        ("::ffff:8.8.8.8", False),
        ("100.64.0.1", False),
        ("0.0.0.0", False),
        ("2001:4860:4860::8888", False),
        (IP_EXTERNO, False),
    ],
)
def test_ip_de_rede_privada_ou_loopback_e_local(vigia_de_rede, host, local):
    assert vigia_de_rede.liberado((host, 80), por_nome=False) is local


@pytest.mark.django_db
def test_nome_de_servico_das_settings_so_vale_para_resolver(vigia_de_rede):
    banco = settings.DATABASES["default"]["HOST"]

    for nome in (banco, settings.REDIS_HOST, "localhost"):
        assert vigia_de_rede.liberado((nome, 80), por_nome=True)

    # a conexão é conferida pelo IP: um nome não abre conexão
    assert not vigia_de_rede.liberado(("cmjredis", 6379), por_nome=False)
    assert not vigia_de_rede.liberado((NOME_EXTERNO, 80), por_nome=True)


@pytest.mark.django_db
def test_socket_de_arquivo_passa(vigia_de_rede):
    assert vigia_de_rede.liberado("/var/run/servico.sock", por_nome=False)
    assert vigia_de_rede.liberado(b"/var/run/servico.sock", por_nome=False)
