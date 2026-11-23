"""Login por usuário e senha pela API (docs/specs/api/login.md)."""

import re
from pathlib import Path

import pytest
import yaml
from django.core.cache import cache
from django.test import Client

URL_SESSAO = "/api/auth/session"
URL_TOKEN = "/api/auth/token"
SENHA = "senha-de-teste-123"
LIMITE = 3
RAIZ = Path(__file__).resolve().parents[3]


@pytest.fixture
def limite(settings):
    """Três tentativas por dia, com cache que guarda a contagem.

    A janela é de um dia para que a virada de janela não zere a contagem no meio
    de um teste.
    """
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "api-limite-login",
        }
    }
    settings.RATE_LIMITER_RATE = f"{LIMITE}/d"
    cache.clear()
    yield LIMITE
    cache.clear()


@pytest.fixture
def usuario(django_user_model):
    return django_user_model.objects.create_user(
        email="limite@exemplo.invalid", password=SENHA
    )


def _entrar(client, url, senha="senha-errada"):
    return client.post(
        url,
        {"username": "limite@exemplo.invalid", "password": senha},
        content_type="application/json",
    )


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-001")
@pytest.mark.parametrize("url", [URL_SESSAO, URL_TOKEN])
def test_login_pela_api_respeita_o_limite_de_tentativas(client, limite, usuario, url):
    for _ in range(limite):
        assert _entrar(client, url).status_code == 400

    resposta = _entrar(client, url)

    assert resposta.status_code == 429
    assert resposta["Retry-After"]


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-001")
@pytest.mark.parametrize("url", [URL_SESSAO, URL_TOKEN])
def test_alem_do_limite_nem_a_credencial_correta_e_avaliada(
    client, limite, usuario, url
):
    for _ in range(limite):
        _entrar(client, url)

    resposta = _entrar(client, url, SENHA)

    assert resposta.status_code == 429
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-002")
def test_as_duas_rotas_compartilham_a_contagem(client, limite, usuario):
    assert _entrar(client, URL_SESSAO).status_code == 400
    assert _entrar(client, URL_TOKEN).status_code == 400
    assert _entrar(client, URL_SESSAO).status_code == 400

    assert _entrar(client, URL_TOKEN).status_code == 429
    assert _entrar(client, URL_SESSAO).status_code == 429


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-003")
def test_consultar_e_encerrar_a_sessao_nao_contam_no_limite(client, limite, usuario):
    for _ in range(limite + 2):
        assert client.get(URL_SESSAO).status_code == 200
        assert client.options(URL_SESSAO).status_code == 200
        assert client.delete(URL_SESSAO).status_code == 200

    assert _entrar(client, URL_SESSAO).status_code == 400


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-004")
def test_dentro_do_limite_o_login_por_sessao_funciona(client, limite, usuario):
    resposta = _entrar(client, URL_SESSAO, SENHA)

    assert resposta.status_code == 200
    assert client.session["_auth_user_id"] == str(usuario.pk)


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-004")
def test_dentro_do_limite_o_login_por_token_funciona(client, limite, usuario):
    resposta = _entrar(client, URL_TOKEN, SENHA)

    assert resposta.status_code == 200
    assert resposta.json()["token"]


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-004")
@pytest.mark.parametrize("url", [URL_SESSAO, URL_TOKEN])
def test_credencial_invalida_dentro_do_limite_responde_400(
    client, limite, usuario, url
):
    resposta = _entrar(client, url)

    assert resposta.status_code == 400
    assert "non_field_errors" in resposta.json()


# ---------------------------------------------------------------------------
# Token CSRF no login por sessão
# ---------------------------------------------------------------------------

CREDENCIAL = {"username": "limite@exemplo.invalid", "password": SENHA}


@pytest.fixture
def cliente_csrf():
    """Cliente que confere o CSRF como um navegador de verdade."""
    return Client(enforce_csrf_checks=True)


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-006")
def test_login_por_sessao_confere_o_token_csrf(cliente_csrf, usuario):
    resposta = cliente_csrf.post(
        URL_SESSAO, CREDENCIAL, content_type="application/json"
    )

    assert resposta.status_code == 403
    assert "_auth_user_id" not in cliente_csrf.session


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-006")
def test_login_por_sessao_confere_o_token_csrf_em_formulario(cliente_csrf, usuario):
    resposta = cliente_csrf.post(URL_SESSAO, CREDENCIAL)

    assert resposta.status_code == 403
    assert "_auth_user_id" not in cliente_csrf.session


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-006")
@pytest.mark.spec("API-AUTH-007")
@pytest.mark.parametrize("url_do_token", ["/api/version", URL_SESSAO])
def test_login_por_sessao_com_o_token_do_cookie_no_cabecalho(
    cliente_csrf, usuario, url_do_token
):
    assert cliente_csrf.get(url_do_token).status_code == 200
    token = cliente_csrf.cookies["csrftoken"].value

    resposta = cliente_csrf.post(
        URL_SESSAO,
        CREDENCIAL,
        content_type="application/json",
        headers={"X-CSRFToken": token},
    )

    assert resposta.status_code == 200
    assert cliente_csrf.session["_auth_user_id"] == str(usuario.pk)


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-006")
def test_login_por_sessao_com_o_token_no_campo_do_formulario(cliente_csrf, usuario):
    cliente_csrf.get(URL_SESSAO)
    token = cliente_csrf.cookies["csrftoken"].value

    resposta = cliente_csrf.post(
        URL_SESSAO, {**CREDENCIAL, "csrfmiddlewaretoken": token}
    )

    assert resposta.status_code == 200
    assert cliente_csrf.session["_auth_user_id"] == str(usuario.pk)


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-006")
def test_encerrar_a_sessao_confere_o_token_csrf(cliente_csrf, usuario):
    cliente_csrf.force_login(usuario)
    cliente_csrf.get(URL_SESSAO)

    assert cliente_csrf.delete(URL_SESSAO).status_code == 403
    assert cliente_csrf.session["_auth_user_id"] == str(usuario.pk)

    token = cliente_csrf.cookies["csrftoken"].value
    resposta = cliente_csrf.delete(URL_SESSAO, headers={"X-CSRFToken": token})

    assert resposta.status_code == 200
    assert "_auth_user_id" not in cliente_csrf.session


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-007")
@pytest.mark.parametrize("url", ["/api/version", URL_SESSAO])
def test_consulta_entrega_o_cookie_csrf_a_quem_ainda_nao_entrou(cliente_csrf, url):
    assert "csrftoken" not in cliente_csrf.cookies

    assert cliente_csrf.get(url).status_code == 200

    assert cliente_csrf.cookies["csrftoken"].value


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-008")
def test_login_por_token_nao_depende_de_csrf(cliente_csrf, usuario):
    resposta = cliente_csrf.post(URL_TOKEN, CREDENCIAL, content_type="application/json")

    assert resposta.status_code == 200
    assert resposta.json()["token"]


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-009")
@pytest.mark.parametrize(
    "conf",
    ["docker/nginx/cmj_docker.conf", "docker/nginx_indev_modprod/cmj_docker.conf"],
)
def test_nginx_do_container_informa_o_ip_do_cliente_nos_tres_blocos(conf):
    texto = (RAIZ / conf).read_text()
    blocos = dict(re.findall(r"location (@proxy_to_\w+) \{(.*?)\n    \}", texto, re.S))

    assert set(blocos) == {"@proxy_to_ws", "@proxy_to_app", "@proxy_to_app_api"}
    for nome, corpo in blocos.items():
        assert "proxy_set_header X-Real-IP $remote_addr;" in corpo, nome
    # o valor informado pelo proxy da frente só vale de conexão local ou privada
    assert "real_ip_header X-Real-IP;" in texto
    aceitos = set(re.findall(r"set_real_ip_from (\S+);", texto))
    assert aceitos == {
        "127.0.0.1",
        "::1",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
    }


@pytest.mark.django_db
@pytest.mark.spec("API-AUTH-009")
def test_containers_de_producao_publicam_a_porta_so_no_loopback():
    compose = yaml.safe_load((RAIZ / "docker/docker-compose.yaml").read_text())
    portas = [
        porta
        for servico in compose["services"].values()
        for porta in servico.get("ports", [])
    ]

    assert portas
    assert all(str(porta).startswith("127.0.0.1:") for porta in portas)
