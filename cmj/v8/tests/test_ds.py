"""Design system do v8 e as rotas de tema (docs/specs/v8/ds.md e temas.md)."""

import inspect
import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from cmj.v8 import views
from cmj.v8.services import s_ds, s_global

from .conftest import (
    DIR_CSS_OFICIAL,
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
def test_design_system_e_publico_e_escolher_tema_exige_superusuario(
    comum, superusuario
):
    for url in URLS_DS:
        for usuario in (None, comum, superusuario):
            resposta = cliente_http(usuario).get(url)
            assert resposta.status_code == 200, (url, usuario)
            assert "private" in resposta["Cache-Control"], url
            # O botão de escolher o tema só aparece para quem pode usá-lo.
            html = html_de(resposta)
            espera_botao = usuario == superusuario and url != URL_VITRINE
            assert ("Usar este tema" in html) is espera_botao, (url, usuario)

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


# --- Conteúdo da vitrine ---------------------------------------------------------------


def vitrine(usuario):
    return html_de(cliente_http(usuario).get(URL_VITRINE))


def secao(html, ancora):
    """O HTML de uma seção da vitrine, do ``<section id>`` ao ``</section>`` que a fecha."""
    inicio = html.index(f'<section id="{ancora}"')
    ancoras = [item.ancora for item in s_ds.SECOES]
    seguintes = ancoras[ancoras.index(ancora) + 1 :]
    fim = (
        html.index(f'<section id="{seguintes[0]}"')
        if seguintes
        else html.index("</main>")
    )
    return html[inicio:fim]


def tokens_do_oficial():
    css = (DIR_CSS_OFICIAL / "tokens.css").read_text("utf-8")
    bloco = css[css.index(":root {") : css.index("\n}")]
    return re.findall(r"(--[a-z][a-z0-9-]*)\s*:", bloco)


def sem_classe(html, tag):
    """Aberturas de ``<tag>`` sem atributo ``class``."""
    return [
        m.group(0)
        for m in re.finditer(rf"<{tag}(?:\s[^>]*)?>", html)
        if "class=" not in m.group(0)
    ]


@pytest.mark.spec("V8-DS-003")
def test_vitrine_tem_amostras_e_rotulos_curtos_sem_texto_explicativo(superusuario):
    miolo = conteudo(vitrine(superusuario))
    miolo = re.sub(r"<pre>.*?</pre>", "", miolo, flags=re.S)
    trechos = [t.strip() for t in re.split(r"<[^>]+>", miolo) if t.strip()]
    assert trechos
    longos = [t for t in trechos if len(t) > 100]
    assert longos == []
    # Os rótulos das amostras são nomes: de classe, de token ou de ícone.
    rotulos = re.findall(r'<code class="text-(?:xs|sm)[^"]*">([^<]+)</code>', miolo)
    assert rotulos
    assert all(re.fullmatch(r"[a-z0-9-]+(, [a-z0-9-]+)*", r) for r in rotulos), rotulos


@pytest.mark.spec("V8-DS-004")
def test_amostras_sao_fixas_e_ficticias(superusuario):
    assert s_ds.amostras() == s_ds.amostras()
    pessoas = s_ds.amostras()["pessoas"]
    assert pessoas
    assert all(p["email"].endswith("@exemplo.invalid") for p in pessoas)
    html = vitrine(superusuario)
    tabelas = secao(html, "ds-tabelas")
    for pessoa in pessoas:
        assert pessoa["nome"] in tabelas and pessoa["email"] in tabelas
    with CaptureQueriesContext(connection) as consultas:
        s_ds.amostras()
    assert len(consultas) == 0


@pytest.mark.spec("V8-DS-005")
def test_todo_token_de_cor_fonte_raio_e_sombra_tem_amostra(superusuario):
    nomes = tokens_do_oficial()
    cores = [n for n in nomes if n.startswith("--cor-")]
    forma = [n for n in nomes if re.match(r"--(fonte|raio|sombra)", n)]
    assert len(cores) >= 20 and len(forma) >= 10
    html = vitrine(superusuario)
    parte_cores = secao(html, "ds-cores")
    for nome in cores:
        assert f"bg-({nome})" in parte_cores, nome
        assert f">{nome}</code>" in parte_cores, nome
    parte_tokens = secao(html, "ds-tokens")
    for nome in forma:
        assert f">{nome}</code>" in parte_tokens, nome


@pytest.mark.spec("V8-DS-006")
def test_elementos_html_aparecem_sem_classe(superusuario):
    miolo = conteudo(vitrine(superusuario))
    tags = (
        "h1 h2 h3 h4 h5 h6 p a strong em mark del ins small sub sup abbr cite q time code "
        "kbd samp blockquote pre hr address figure figcaption details summary ul ol li dl "
        "dt dd table caption thead tbody tfoot tr th td fieldset legend label select "
        "optgroup option textarea datalist progress meter output button"
    ).split()
    for tag in tags:
        assert sem_classe(miolo, tag), tag
    entradas = sem_classe(miolo, "input")
    tipos = (
        "text search email url tel password number date time datetime-local month week "
        "color range file checkbox radio submit reset button"
    ).split()
    for tipo in tipos:
        assert any(f'type="{tipo}"' in e for e in entradas), tipo
    for estado in ("disabled", "readonly", "required", 'aria-invalid="true"'):
        assert any(estado in e for e in entradas), estado
    assert any("multiple" in s for s in sem_classe(miolo, "select"))


@pytest.mark.spec("V8-DS-007")
def test_toda_classe_de_componentes_css_aparece(superusuario):
    css = (DIR_CSS_OFICIAL / "componentes.css").read_text("utf-8")
    classes = sorted(set(re.findall(r"\.(v8-[a-z0-9-]+)", css)))
    assert len(classes) > 20
    html = vitrine(superusuario)
    usadas = {
        nome
        for atributo in re.findall(r'class="([^"]*)"', html)
        for nome in atributo.split()
    }
    assert [c for c in classes if c not in usadas] == []


@pytest.mark.spec("V8-DS-008")
def test_todo_icone_do_sprite_aparece_com_o_nome(superusuario):
    sprite = (DIR_TEMPLATES_V8 / "v8" / "shell" / "icones.html").read_text("utf-8")
    assert re.findall(r'<symbol id="v8-i-([a-z-]+)"', sprite) == list(s_ds.ICONES)
    parte = secao(vitrine(superusuario), "ds-icones")
    for nome in s_ds.ICONES:
        assert f'href="#v8-i-{nome}"></use></svg><code' in parte, nome
        assert f">{nome}</code>" in parte, nome


@pytest.mark.spec("V8-DS-009")
def test_drawers_por_gatilho_e_modals_e_toasts_pela_ilha(superusuario):
    html = vitrine(superusuario)
    drawers = secao(html, "ds-drawers")
    gatilhos = re.findall(r"<a [^>]*data-drawer=[^>]*>", drawers)
    assert len(gatilhos) >= 8

    def valores(atributo):
        return {
            m.group(1)
            for g in gatilhos
            for m in [re.search(rf'{atributo}="([^"]+)"', g)]
            if m
        }

    assert valores("data-drawer-side") == {"left", "right"}
    assert {"sm", "md", "lg"} <= valores("data-drawer-size")
    assert valores("data-drawer-mode") == {"overlay", "push", "docked"}
    assert valores("data-drawer-scrim") == {"false"}
    assert 'data-confirm="' in drawers and 'data-confirm-variant="perigo"' in drawers
    assert 'data-vue-island="ds-overlays"' in secao(html, "ds-overlays")


@pytest.mark.spec("V8-DS-010")
def test_sem_javascript_as_secoes_em_html_ficam_completas(superusuario):
    html = vitrine(superusuario)
    com_ilha = {
        "overlays",
        "componentes",
        "campos",
        "estrutura",
        "datas",
        "seletores-cor",
    }
    for item in s_ds.SECOES:
        parte = secao(html, item.ancora)
        if item.id in com_ilha:
            ilha = parte[parte.index("data-vue-island=") :]
            assert '<p class="v8-alerta v8-alerta-aviso">' in ilha, item.id
        else:
            assert "data-vue-island" not in parte, item.id
    # Sem JavaScript, os gatilhos levam ao conteúdo do drawer na própria página.
    drawers = secao(html, "ds-drawers")
    destinos = set(re.findall(r'<a [^>]*href="([^"]+)"[^>]*data-drawer=', drawers))
    assert destinos == {"#ds-drawer-conteudo"}
    assert drawers.count('id="ds-drawer-conteudo"') == 1
