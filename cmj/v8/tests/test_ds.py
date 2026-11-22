"""Design system do v8 e as rotas de tema (docs/specs/v8/ds.md e temas.md)."""

import inspect
import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from cmj.v8 import views
from cmj.v8.services import s_ds, s_global

from .conftest import (
    DIR_TEMPLATES_V8,
    URLS_DS,
    cliente_http,
    html_de,
    ler_json_script,
)

pytestmark = pytest.mark.django_db

URL_VITRINE = "/v8/ds/"
URL_TEMAS = "/v8/ds/temas/"


def url_previa(nome):
    return f"/v8/ds/temas/{nome}/"


def url_usar(nome):
    return f"/v8/ds/temas/{nome}/usar/"


def atributos_html(html):
    return re.search(r"<html[^>]*>", html).group(0)


def conteudo(html):
    """O miolo da página, sem o shell: do ``<div class="v8-conteudo">`` ao fim do ``<main>``."""
    return html[html.index('<div class="v8-conteudo">') : html.index("</main>")]


# --- Vitrine -----------------------------------------------------------------------


@pytest.mark.spec("V8-DS-001")
def test_vitrine_e_pagina_no_app_sidebar_no_tema_em_vigor(superusuario):
    cliente = cliente_http(superusuario)
    resposta = cliente.get(URL_VITRINE)
    assert resposta.status_code == 200
    nomes = [t.name for t in resposta.templates]
    assert nomes[0] == "v8/ds/vitrine.html"
    assert "v8/layouts/app_sidebar.html" in nomes
    html = html_de(resposta)
    assert 'data-v8-layout="app_sidebar"' in html
    assert 'data-tema="oficial"' in atributos_html(html)
    assert '<h1 class="v8-pagina-titulo">Design system</h1>' in html

    cliente.cookies["v8_tema"] = "tema2"
    cliente.cookies["v8_modo"] = "escuro"
    html = html_de(cliente.get(URL_VITRINE))
    assert 'data-tema="tema2" data-modo="escuro"' in atributos_html(html)
    assert "data-ds-previa" not in html


@pytest.mark.spec("V8-DS-002")
def test_secoes_vem_do_registro_com_ancora_e_indice(superusuario):
    assert s_ds.SECOES
    ids = [secao.id for secao in s_ds.SECOES]
    assert len(ids) == len(set(ids))
    pasta = DIR_TEMPLATES_V8 / "v8" / "partials" / "ds"
    # Toda parcial da pasta é de uma seção do registro, e vice-versa.
    assert sorted(p.stem for p in pasta.glob("*.html")) == sorted(ids)

    html = html_de(cliente_http(superusuario).get(URL_VITRINE))
    indice = html[html.index('aria-label="Seções da vitrine"') :]
    indice = indice[: indice.index("</nav>")]
    assert re.findall(r'href="#(ds-[a-z-]+)"', indice) == [f"ds-{i}" for i in ids]
    posicoes = []
    for secao in s_ds.SECOES:
        assert secao.ancora == f"ds-{secao.id}"
        assert secao.parcial == f"v8/partials/ds/{secao.id}.html"
        marca = f'<section id="{secao.ancora}"'
        assert html.count(marca) == 1, secao.id
        posicoes.append(html.index(marca))
        assert f">{secao.rotulo}</h2>" in html, secao.id
    assert posicoes == sorted(posicoes)


@pytest.mark.spec("V8-DS-013")
def test_previa_e_a_vitrine_no_tema_com_faixa_e_botao(superusuario):
    cliente = cliente_http(superusuario)
    for nome, rotulo in s_global.TEMAS.items():
        resposta = cliente.get(url_previa(nome))
        assert resposta.status_code == 200, nome
        assert [t.name for t in resposta.templates][0] == "v8/ds/vitrine.html"
        html = html_de(resposta)
        assert f'data-tema="{nome}"' in atributos_html(html), nome
        assert f'data-ds-previa="{nome}"' in html
        assert f'action="{url_usar(nome)}"' in html
        assert ">Usar este tema</button>" in html
        assert f'href="{URL_TEMAS}"' in conteudo(html)
        assert f'<h1 class="v8-pagina-titulo">{rotulo}</h1>' in html
        # As mesmas seções da vitrine.
        for secao in s_ds.SECOES:
            assert f'<section id="{secao.ancora}"' in html
        # A trilha leva de volta à lista de temas.
        assert f'<li><a href="{URL_TEMAS}">Temas</a></li>' in html

    # A prévia vence o tema escolhido no navegador.
    cliente.cookies["v8_tema"] = "tema1"
    assert 'data-tema="tema3"' in atributos_html(
        html_de(cliente.get(url_previa("tema3")))
    )


# --- Temas ------------------------------------------------------------------------


@pytest.mark.spec("V8-TEMA-024")
def test_lista_de_temas_marca_o_tema_em_vigor(superusuario):
    cliente = cliente_http(superusuario)
    html = html_de(cliente.get(URL_TEMAS))
    nomes = re.findall(r'data-ds-tema="([^"]+)"', html)
    assert nomes == list(s_global.TEMAS)
    for nome, rotulo in s_global.TEMAS.items():
        assert f">{rotulo}</h2>" in html
        assert f'href="{url_previa(nome)}"' in html
        assert f'action="{url_usar(nome)}"' in html
    marcado = re.findall(r'data-ds-tema="([^"]+)" aria-current="true"', html)
    assert marcado == ["oficial"]

    cliente.cookies["v8_tema"] = "tema2"
    html = html_de(cliente.get(URL_TEMAS))
    assert re.findall(r'data-ds-tema="([^"]+)" aria-current="true"', html) == ["tema2"]


@pytest.mark.spec("V8-TEMA-022")
def test_previa_nao_grava_nada(superusuario):
    cliente = cliente_http(superusuario)
    for nome in s_global.TEMAS:
        resposta = cliente.get(url_previa(nome))
        assert set(resposta.cookies) <= {"csrftoken"}, nome
    assert "v8_tema" not in cliente.cookies
    # Depois das prévias, as outras páginas seguem no oficial.
    assert 'data-tema="oficial"' in atributos_html(html_de(cliente.get(URL_TEMAS)))


@pytest.mark.spec("V8-TEMA-023")
def test_usar_um_tema_grava_o_cookie_e_vale_em_todo_o_v8(superusuario):
    cliente = cliente_http(superusuario)
    resposta = cliente.post(url_usar("tema2"))
    assert resposta.status_code == 302
    assert resposta["Location"] == URL_TEMAS
    assert resposta.cookies["v8_tema"].value == "tema2"

    seguinte = cliente.get(resposta["Location"])
    html = html_de(seguinte)
    assert 'data-tema="tema2"' in atributos_html(html)
    mensagens = ler_json_script(html, "v8-messages")
    assert mensagens == [
        {"nivel": "success", "texto": "Tema 2 em uso neste navegador."}
    ]

    for url in ("/v8/", "/v8/demo/clientes/", URL_VITRINE, "/v8/nao-existe/"):
        html = html_de(cliente.get(url))
        assert 'data-tema="tema2"' in atributos_html(html), url
        assert ler_json_script(html, "v8-global")["tema"] == "tema2", url

    # Voltar ao padrão é usar o oficial.
    cliente.post(url_usar("oficial"))
    assert 'data-tema="oficial"' in atributos_html(html_de(cliente.get("/v8/")))


# --- Requisitos de segurança ---------------------------------------------------------


@pytest.mark.spec("V8-DS-040")
@pytest.mark.spec("V8-TEMA-041")
def test_design_system_e_escolha_de_tema_exigem_superusuario(comum, superusuario):
    for url in URLS_DS:
        anonimo = cliente_http().get(url)
        assert anonimo.status_code == 302, url
        assert anonimo["Location"].startswith("/login/?next=/v8/ds/"), url
        assert cliente_http(comum).get(url).status_code == 403, url
        assert cliente_http(superusuario).get(url).status_code == 200, url

    for nome in s_global.TEMAS:
        anonimo = cliente_http().post(url_usar(nome))
        assert anonimo.status_code == 302
        assert anonimo["Location"].startswith("/login/?next=")
        assert "v8_tema" not in anonimo.cookies
        negado = cliente_http(comum).post(url_usar(nome))
        assert negado.status_code == 403
        assert "v8_tema" not in negado.cookies


@pytest.mark.spec("V8-DS-041")
@pytest.mark.spec("V8-TEMA-041")
def test_paginas_so_aceitam_get_e_head_e_usar_so_post_com_csrf(superusuario):
    cliente = cliente_http(superusuario)
    for url in URLS_DS:
        assert cliente.head(url).status_code == 200, url
        for metodo in ("post", "put", "patch", "delete"):
            assert getattr(cliente, metodo)(url).status_code == 405, (metodo, url)
    for nome in s_global.TEMAS:
        for metodo in ("get", "head", "put", "patch", "delete"):
            resposta = getattr(cliente, metodo)(url_usar(nome))
            assert resposta.status_code == 405, (metodo, nome)
            assert "v8_tema" not in resposta.cookies

    rigoroso = cliente_http(superusuario, enforce_csrf_checks=True)
    sem_token = rigoroso.post(url_usar("tema1"))
    assert sem_token.status_code == 403
    assert "v8_tema" not in sem_token.cookies
    rigoroso.get(URL_TEMAS)
    token = rigoroso.cookies["csrftoken"].value
    com_token = rigoroso.post(url_usar("tema1"), {"csrfmiddlewaretoken": token})
    assert com_token.status_code == 302
    assert com_token.cookies["v8_tema"].value == "tema1"
    assert views.DsTemaUsarView.http_method_names == ["post"]


@pytest.mark.spec("V8-TEMA-040")
def test_nome_de_tema_fora_do_registro_nao_tem_rota_nem_vale(superusuario):
    cliente = cliente_http(superusuario)
    for nome in ("zzqx", "Oficial", "escuro", "tema1x", "..", "tema%20"):
        assert cliente.get(f"/v8/ds/temas/{nome}/").status_code == 404, nome
        resposta = cliente.post(f"/v8/ds/temas/{nome}/usar/")
        assert resposta.status_code == 404, nome
        assert "v8_tema" not in resposta.cookies
    assert s_global.cookie_tema("zzqx") is None
    assert s_global.cookie_tema("escuro") is None

    cliente.cookies["v8_tema"] = 'zzqx"><b>'
    for url in (URL_VITRINE, URL_TEMAS, "/v8/"):
        html = html_de(cliente.get(url))
        assert "zzqx" not in html, url
        assert 'data-tema="oficial"' in atributos_html(html), url


@pytest.mark.spec("V8-TEMA-042")
def test_destino_depois_de_usar_um_tema_e_fixo(superusuario):
    cliente = cliente_http(superusuario)
    for extra in (
        {"path": url_usar("tema1") + "?next=https://exemplo.invalid/"},
        {"path": url_usar("tema1"), "data": {"next": "//exemplo.invalid/"}},
        {"path": url_usar("tema1"), "headers": {"Referer": "https://exemplo.invalid/"}},
    ):
        resposta = cliente.post(**extra)
        assert resposta.status_code == 302
        assert resposta["Location"] == URL_TEMAS


@pytest.mark.spec("V8-TEMA-043")
@pytest.mark.parametrize("debug", [False, True])
def test_cookie_de_tema_tem_os_atributos_de_preferencia(superusuario, settings, debug):
    settings.DEBUG = debug
    resposta = cliente_http(superusuario).post(url_usar("tema3"))
    cookie = resposta.cookies["v8_tema"]
    assert cookie.value == "tema3"
    assert cookie["path"] == "/v8/"
    assert cookie["samesite"] == "Lax"
    assert cookie["httponly"] is True
    assert bool(cookie["secure"]) is (not debug)
    assert int(cookie["max-age"]) > 0


@pytest.mark.spec("V8-DS-042")
def test_nada_da_requisicao_e_renderizado_na_vitrine(superusuario):
    cliente = cliente_http(superusuario)
    for url in URLS_DS:
        html = html_de(cliente.get(url + "?secao=zzqx&tema=zzqy&parcial=zzqw"))
        assert "zzqx" not in html and "zzqy" not in html and "zzqw" not in html, url
    fonte = (DIR_TEMPLATES_V8 / "v8" / "ds" / "vitrine.html").read_text("utf-8")
    assert re.findall(r"{%\s*include\s+([^%]+?)\s*%}", fonte) == ["secao.parcial"]
    assert isinstance(s_ds.SECOES, tuple)
    for secao in s_ds.SECOES:
        assert re.fullmatch(r"[a-z][a-z-]*", secao.id)


@pytest.mark.spec("V8-DS-043")
def test_design_system_nao_le_nem_grava_model_arquivo_cache_fila_ou_indice(
    superusuario,
):
    fonte = inspect.getsource(s_ds)
    for proibido in (
        "models",
        "django.db",
        "cache",
        "celery",
        "haystack",
        "open(",
        "storage",
        "pathlib",
        "import os",
        "subprocess",
    ):
        assert proibido not in fonte, proibido
    with CaptureQueriesContext(connection) as consultas:
        s_ds.temas("tema1")
        s_ds.tema("tema2", "oficial")
    assert len(consultas) == 0
