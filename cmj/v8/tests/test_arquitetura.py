"""Testes da spec docs/specs/v8/arquitetura.md.

Cada teste está ligado a uma regra pelo marker ``spec``.
"""

import inspect
import json
import re
from pathlib import Path

import pytest
from django.apps import apps
from django.conf import settings
from django.template import engines
from django.template.loader import render_to_string
from django.urls import resolve

import cmj.v8.urls
from cmj.v8 import views
from cmj.v8.services import s_demo, s_ds, s_global, s_menu, s_respostas
from cmj.v8.tests.conftest import (
    CABECALHOS_CLIENTE,
    DIR_TEMPLATES_V8,
    URL_DEMO_FRAGMENTO,
    URLS_DEMO_API,
    URLS_DEMO_LAYOUTS,
    URLS_DEMO_PAGINAS,
    URLS_DS,
    cliente_http,
    criar_usuario,
    html_de,
    ler_json_script,
    renderizar,
    templates_v8,
)

pytestmark = pytest.mark.django_db

DIR_APP = Path(cmj.v8.urls.__file__).parent
CHAVES_GLOBAIS = {
    "versao",
    "debug",
    "autenticado",
    "usuario",
    "permissoes",
    "urls",
    "zonas",
    "zona",
    "flags",
    "tema",
    "modo",
    "sidebar",
}
NOME_HOSTIL_1 = "</script><script>alert(1)"
NOME_HOSTIL_2 = "</script>\"'&"


# --- Contenção ---------------------------------------------------------------


@pytest.mark.spec("V8-ARQ-001")
def test_toda_rota_do_app_comeca_por_v8():
    assert cmj.v8.urls.urlpatterns
    for rota in cmj.v8.urls.urlpatterns:
        assert rota.pattern.regex.pattern.startswith("^v8/"), rota

    for fora in ["/", "/v6/x", "/app/x", "/v8", "/v80/", "/xv8/", "/sistema/"]:
        assert not resolve(fora).func.__module__.startswith("cmj.v8"), fora


@pytest.mark.spec("V8-ARQ-002")
def test_rotas_que_ja_existiam_continuam_nas_mesmas_views():
    from cmj.core.views import app_vue_view_v6, app_vue_view_v2018
    from cmj.globalrules.views import manifest, service_worker_proxy

    assert resolve("/v6/qualquer").func is app_vue_view_v6
    assert resolve("/app/qualquer").func is app_vue_view_v2018
    assert resolve("/v8/service-worker.js").func is service_worker_proxy
    assert resolve("/v8/manifest.json").func is manifest
    assert resolve("/v6/manifest.json").func is manifest
    assert resolve("/admin/").view_name == "admin:index"
    for fora_do_v8 in ["/um-caminho-do-portal", "/v8", "/v8x/pagina"]:
        assert resolve(fora_do_v8).view_name == "cmj.sigad:path_view"


@pytest.mark.spec("V8-ARQ-003")
def test_templates_do_v8_nao_encobrem_nem_sao_encobertos():
    assert sorted(p.name for p in DIR_TEMPLATES_V8.iterdir()) == ["base_v8.html", "v8"]

    outros = [Path(d) for d in settings.TEMPLATES[0]["DIRS"]]
    outros += [Path(app.path) / "templates" for app in apps.get_app_configs()]
    outros = [d for d in outros if d.resolve() != DIR_TEMPLATES_V8.resolve()]
    assert len(outros) > 10

    relativos = [p.relative_to(DIR_TEMPLATES_V8) for p in templates_v8()]
    assert len(relativos) > 10
    repetidos = [
        str(outro / relativo)
        for outro in outros
        for relativo in relativos
        if (outro / relativo).exists()
    ]
    assert repetidos == []


@pytest.mark.spec("V8-ARQ-004")
def test_django_nao_cria_cookie_de_preferencia_e_os_nomes_tem_prefixo():
    assert s_global.COOKIE_MODO.startswith("v8_")
    assert s_global.COOKIE_SIDEBAR.startswith("v8_")
    assert s_global.COOKIE_TEMA.startswith("v8_")
    assert s_global.cookie_tema("tema1")["path"] == "/v8/"

    resposta = cliente_http().get("/v8/")
    assert set(resposta.cookies) <= {"csrftoken"}


@pytest.mark.spec("V8-ARQ-006")
def test_app_nao_tem_models_nem_migrations():
    config = apps.get_app_config("v8")
    assert config.name == "cmj.v8"
    assert list(config.get_models()) == []
    assert not (DIR_APP / "migrations").exists()
    assert not (DIR_APP / "models.py").exists()


# --- Rotas Django ------------------------------------------------------------


@pytest.mark.spec("V8-ARQ-010")
def test_inicio_responde_200_no_layout_landing():
    resposta = cliente_http().get("/v8/")
    html = html_de(resposta)
    assert resposta.status_code == 200
    assert '<div class="v8-shell" data-v8-layout="landing">' in html
    assert '<h1 class="v8-pagina-titulo">PortalCMJ</h1>' in html


@pytest.mark.spec("V8-ARQ-011")
def test_zona_responde_no_prefixo_e_em_qualquer_subcaminho(superusuario):
    zona = s_global.ZONAS["demo-spa"]
    assert zona.prefixo == "demo/spa"
    # Declarada uma única vez: as rotas saem do registro.
    rotas_de_zona = [
        r for r in cmj.v8.urls.urlpatterns if (r.name or "").startswith("zona_")
    ]
    assert len(rotas_de_zona) == len(s_global.ZONAS)

    cliente = cliente_http(superusuario)
    for caminho in [
        "/v8/demo/spa",
        "/v8/demo/spa/",
        "/v8/demo/spa/clientes/7",
        "/v8/demo/spa/clientes/7/pedidos/701/",
    ]:
        resposta = cliente.get(caminho)
        html = html_de(resposta)
        assert resposta.status_code == 200, caminho
        assert '<div class="v8-zona" data-vue-zone="demo-spa">' in html
        assert '<div class="v8-shell" data-v8-layout="app_sidebar">' in html
        assert ler_json_script(html, "v8-global")["zona"] == "demo-spa"

    # Só o prefixo exato: um caminho parecido não é da zona.
    assert cliente.get("/v8/demo/spammer/").status_code == 404


@pytest.mark.spec("V8-ARQ-012")
def test_caminho_desconhecido_responde_404_no_layout_minimal():
    for caminho in ["/v8/nao-existe/", "/v8/nao/existe.png", "/v8/_frag/nada/"]:
        resposta = cliente_http().get(caminho)
        html = html_de(resposta)
        assert resposta.status_code == 404, caminho
        assert '<main id="conteudo" class="v8-nua" data-v8-layout="minimal">' in html
        assert 'class="v8-shell"' not in html
        assert "Página não encontrada" in html


@pytest.mark.spec("V8-ARQ-013")
def test_paginas_e_fragmentos_tem_url_terminada_em_barra(superusuario):
    cliente = cliente_http(superusuario)
    for com_barra in ["/v8/demo/clientes/", "/v8/demo/clientes/1/", URL_DEMO_FRAGMENTO]:
        assert cliente.get(com_barra).status_code == 200
        assert cliente.get(com_barra.rstrip("/")).status_code == 404

    nomes_de_zona = {f"zona_{nome}" for nome in s_global.ZONAS}
    for rota in cmj.v8.urls.urlpatterns:
        if rota.name in nomes_de_zona or rota.name == "nao_encontrado":
            continue
        assert rota.pattern.regex.pattern.endswith("/$"), rota


@pytest.mark.spec("V8-ARQ-014")
def test_servicos_nao_recebem_a_requisicao():
    for modulo in (s_global, s_menu, s_demo, s_ds, s_respostas):
        assert "request" not in inspect.getsource(modulo), modulo.__name__
        for nome, funcao in inspect.getmembers(modulo, inspect.isfunction):
            if funcao.__module__ != modulo.__name__:
                continue
            assert "request" not in inspect.signature(funcao).parameters, nome

    assert list(inspect.signature(s_global.dados_globais).parameters) == [
        "usuario",
        "zona",
        "preferencias",
    ]
    assert list(inspect.signature(s_menu.menu_para).parameters) == ["usuario", "ativo"]


# --- Templates ---------------------------------------------------------------


@pytest.mark.spec("V8-ARQ-022")
@pytest.mark.parametrize("layout", ["landing", "app_topbar", "app_sidebar", "minimal"])
def test_layout_renderiza_so_com_os_context_processors(layout, comum):
    fonte = (
        f'{{% extends "v8/layouts/{layout}.html" %}}'
        "{% block content %}{{ block.super }}<p>conteúdo da página</p>{% endblock %}"
    )
    for usuario in (None, comum):
        html = renderizar(fonte, usuario=usuario)
        assert "<p>conteúdo da página</p>" in html
        dados = ler_json_script(html, "v8-global")
        assert dados["autenticado"] is (usuario is not None)
        assert dados["zona"] is None
        assert ler_json_script(html, "v8-messages") == []

    # Nem a requisição é obrigatória.
    assert 'id="v8-global"' in render_to_string(f"v8/layouts/{layout}.html")


@pytest.mark.spec("V8-ARQ-023")
def test_dados_globais_tem_exatamente_as_chaves_previstas(superusuario):
    anonimo = ler_json_script(html_de(cliente_http().get("/v8/")), "v8-global")
    assert set(anonimo) == CHAVES_GLOBAIS
    assert anonimo["versao"] == settings.PORTALCMJ_VERSION
    assert anonimo["debug"] is settings.DEBUG
    assert anonimo["autenticado"] is False
    assert anonimo["urls"] == {
        "api": "/api",
        "versao": "/api/version",
        "sessao": "/api/auth/session",
        "login": "/login/",
        "logout": "/logout/",
        "base": "/v8/",
        "frag": "/v8/_frag/",
    }
    assert anonimo["zonas"] == {"demo-spa": "/v8/demo/spa"}
    assert anonimo["zona"] is None
    assert anonimo["flags"] == {}
    assert anonimo["tema"] == "oficial"
    assert anonimo["modo"] is None
    assert anonimo["sidebar"] == "expandida"

    cliente = cliente_http(superusuario)
    cliente.cookies["v8_modo"] = "escuro"
    cliente.cookies["v8_sidebar"] = "recolhida"
    dados = ler_json_script(html_de(cliente.get("/v8/demo/spa/")), "v8-global")
    assert set(dados) == CHAVES_GLOBAIS
    assert dados["autenticado"] is True
    assert set(dados["usuario"]) == {"id", "username", "nome", "avatar"}
    assert dados["usuario"]["id"] == superusuario.pk
    assert dados["usuario"]["nome"] == "Sofia Super"
    assert dados["usuario"]["avatar"] is None
    assert dados["permissoes"] == sorted(superusuario.get_all_permissions())
    assert dados["permissoes"]
    assert dados["zona"] == "demo-spa"
    assert dados["tema"] == "oficial"
    assert dados["modo"] == "escuro"
    assert dados["sidebar"] == "recolhida"

    # O conteúdo vem do serviço.
    assert dados == json.loads(
        json.dumps(
            s_global.dados_globais(
                superusuario,
                zona="demo-spa",
                preferencias={
                    "tema": "oficial",
                    "modo": "escuro",
                    "sidebar": "recolhida",
                },
            )
        )
    )


@pytest.mark.spec("V8-ARQ-024")
def test_mensagens_do_django_vao_para_o_json(superusuario):
    cliente = cliente_http(superusuario)
    html = html_de(cliente.get("/v8/demo/clientes/"))
    assert ler_json_script(html, "v8-messages") == []

    cliente.post("/v8/demo/clientes/arquivar/", {"ids": ["1", "2"]})
    html = html_de(cliente.get("/v8/demo/clientes/"))
    assert ler_json_script(html, "v8-messages") == [
        {
            "nivel": "success",
            "texto": "2 cliente(s) arquivado(s). Demonstração: nada foi gravado.",
        }
    ]
    # Lida uma vez, a mensagem não volta na página seguinte.
    html = html_de(cliente.get("/v8/demo/clientes/"))
    assert ler_json_script(html, "v8-messages") == []


@pytest.mark.spec("V8-ARQ-025")
@pytest.mark.spec("V8-ARQ-036")
def test_ilha_emite_elemento_props_e_html_de_espera():
    interno = engines["django"].from_string(
        '{% load v8_tags %}{% v8_island "interna" props %}dentro{% endv8_island %}'
    )
    html = renderizar(
        "{% load v8_tags %}"
        '{% v8_island "com-props" props %}<p>espera</p>{% endv8_island %}'
        '{% v8_island "sem-props" %}<p>só html</p>{% endv8_island %}'
        "{% include interno %}"
        "{% v8_island nome outras %}fim{% endv8_island %}",
        contexto={
            "props": {"texto": "</script><b>&\"'", "n": 1},
            "outras": [1, 2],
            "nome": 'a"b',
            "interno": interno.template,
        },
    )

    assert (
        '<div data-vue-island="com-props" data-props-id="v8-island-1">'
        "<p>espera</p></div>" in html
    )
    assert '<div data-vue-island="sem-props"><p>só html</p></div>' in html
    assert '<div data-vue-island="interna" data-props-id="v8-island-2">' in html
    assert '<div data-vue-island="a&quot;b" data-props-id="v8-island-3">fim' in html

    # Ids únicos na página, inclusive com ilha em template incluído.
    ids = re.findall(r'data-props-id="([^"]+)"', html)
    assert ids == ["v8-island-1", "v8-island-2", "v8-island-3"]
    assert ler_json_script(html, "v8-island-1") == {
        "texto": "</script><b>&\"'",
        "n": 1,
    }
    assert ler_json_script(html, "v8-island-3") == [1, 2]
    # Só json_script: nenhum </script> além dos três fechamentos.
    assert html.count("</script>") == 3


@pytest.mark.spec("V8-ARQ-026")
def test_conteudo_e_html_do_servidor_navegavel_sem_javascript(superusuario):
    html = html_de(cliente_http(superusuario).get("/v8/demo/clientes/"))
    conteudo = html[html.index('<div class="v8-conteudo">') :]
    primeiros = s_demo.listar()["itens"]
    assert len(primeiros) == 10
    for cliente in primeiros:
        assert f'<a href="/v8/demo/clientes/{cliente["id"]}/"' in conteudo
        assert f'>{cliente["nome"]}</a>' in conteudo
        assert cliente["email"] in conteudo
    assert '<table class="v8-tabela">' in conteudo
    assert 'method="get" action="/v8/demo/clientes/"' in conteudo


@pytest.mark.spec("V8-ARQ-027")
def test_mesmo_html_com_dummycache_e_com_cache_real(superusuario, settings):
    from django.core.cache import cache

    def paginas():
        saida = []
        for usuario in (None, superusuario):
            for url in ("/v8/", "/v8/demo/clientes/?situacao=inativo"):
                html = html_de(cliente_http(usuario).get(url))
                # O token CSRF mascarado muda a cada requisição.
                html = re.sub(
                    r'name="csrfmiddlewaretoken" value="[^"]+"', "TOKEN", html
                )
                saida.append(html)
        return saida

    assert "dummy" in settings.CACHES["default"]["BACKEND"]
    com_dummy = paginas()

    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "v8-test-arq-027",
        }
    }
    cache.clear()
    try:
        primeira_vez = paginas()
        ja_em_cache = paginas()
    finally:
        cache.clear()

    assert com_dummy == primeira_vez == ja_em_cache


# --- Requisitos de segurança --------------------------------------------------


@pytest.mark.spec("V8-ARQ-060")
def test_json_global_nao_expoe_dado_pessoal_nem_de_sessao(superusuario):
    anonimo = ler_json_script(html_de(cliente_http().get("/v8/")), "v8-global")
    assert anonimo["usuario"] is None
    assert anonimo["permissoes"] == []

    cliente = cliente_http(superusuario)
    html = html_de(cliente.get("/v8/"))
    dados = ler_json_script(html, "v8-global")
    assert set(dados) == CHAVES_GLOBAIS
    assert set(dados["usuario"]) == {"id", "username", "nome", "avatar"}

    bruto = json.dumps(dados)
    assert superusuario.email not in html
    assert "@" not in bruto
    assert cliente.session.session_key not in html
    assert cliente.cookies["csrftoken"].value not in bruto
    assert "password" not in bruto and "senha" not in bruto

    # Usuário sem nome: o identificador exibido não é o e-mail.
    sem_nome = criar_usuario("sem.nome")
    dados = s_global.dados_globais(sem_nome)
    assert dados["usuario"]["nome"] == "sem.nome"
    assert "@" not in json.dumps(dados)


@pytest.mark.spec("V8-ARQ-061")
def test_json_fora_de_cache_e_paginas_com_cache_control_private(
    superusuario, comum, cache_real
):
    # Nenhum trecho em {% cache %} contém os JSON nem o token CSRF.
    for arquivo in templates_v8():
        fonte = arquivo.read_text(encoding="utf-8")
        for bloco in re.findall(r"{% cache .*?{% endcache %}", fonte, re.S):
            assert "v8_dados_globais" not in bloco, arquivo
            assert "v8_mensagens" not in bloco, arquivo
            assert "csrf_token" not in bloco, arquivo

    # Com cache real, cada usuário recebe os próprios dados.
    for usuario in (superusuario, comum, None, superusuario):
        dados = ler_json_script(html_de(cliente_http(usuario).get("/v8/")), "v8-global")
        if usuario is None:
            assert dados["usuario"] is None
        else:
            assert dados["usuario"]["id"] == usuario.pk

    respostas = [
        cliente_http().get("/v8/"),
        cliente_http().get("/v8/nao-existe/"),
        cliente_http(comum).get("/v8/demo/clientes/"),
        cliente_http(superusuario).get("/v8/demo/clientes/"),
        cliente_http(superusuario).get("/v8/demo/spa/"),
    ]
    assert [r.status_code for r in respostas] == [200, 404, 403, 200, 200]
    for resposta in respostas:
        assert "private" in resposta["Cache-Control"]
        assert "public" not in resposta["Cache-Control"]


@pytest.mark.spec("V8-ARQ-062")
def test_dado_do_servidor_so_chega_ao_javascript_por_json_script():
    hostil = criar_usuario(
        "hostil",
        superusuario=True,
        first_name=NOME_HOSTIL_1,
        last_name=NOME_HOSTIL_2,
    )
    nome = f"{NOME_HOSTIL_1} {NOME_HOSTIL_2}"
    assert nome == "</script><script>alert(1) </script>\"'&"

    for url in ("/v8/", "/v8/demo/clientes/", "/v8/demo/spa/"):
        html = html_de(cliente_http(hostil).get(url))
        # O valor chega idêntico ao original.
        assert ler_json_script(html, "v8-global")["usuario"]["nome"] == nome
        # Nenhum <script> a mais nem a menos: o nome não abriu nem fechou tag.
        assert "<script>" not in html
        assert html.count("</script>") == html.count("<script ")
        assert "&lt;/script&gt;&lt;script&gt;alert(1)" in html

    # Nos templates não há <script> escrito à mão, |safe, autoescape desligado,
    # manipulador de evento em atributo nem estilo em linha.
    for arquivo in templates_v8():
        fonte = arquivo.read_text(encoding="utf-8")
        assert "<script" not in fonte, arquivo
        assert "|safe" not in fonte, arquivo
        assert "autoescape" not in fonte, arquivo
        assert not re.search(r"\son[a-z]+\s*=", fonte), arquivo
        assert "style=" not in fonte, arquivo


@pytest.mark.spec("V8-ARQ-065")
@pytest.mark.spec("V8-SHELL-050")
def test_servidor_confere_o_acesso_de_cada_rota_escondida_no_menu(comum, superusuario):
    urls_do_menu = [
        filho.url
        for item in s_menu.MENU
        for filho in item.filhos
        if filho.permissao == s_global.SUPERUSUARIO
    ]
    assert urls_do_menu == [
        "/v8/demo/clientes/",
        "/v8/demo/spa/",
        *URLS_DEMO_LAYOUTS,
    ]

    for url in urls_do_menu + URLS_DEMO_PAGINAS + [URL_DEMO_FRAGMENTO]:
        anonimo = cliente_http().get(url)
        assert anonimo.status_code == 302, url
        assert anonimo["Location"].startswith("/login/?next=/v8/"), url
        assert cliente_http(comum).get(url).status_code == 403, url
        assert cliente_http(superusuario).get(url).status_code == 200, url

    for url in URLS_DEMO_API:
        assert cliente_http().get(url).status_code == 401, url
        resposta = cliente_http(comum).get(url, headers=CABECALHOS_CLIENTE)
        assert resposta.status_code == 403, url
        assert resposta.json()["code"] == "sem_permissao"


@pytest.mark.spec("V8-ARQ-066")
def test_paginas_zonas_e_fragmentos_aceitam_so_get_e_head(superusuario):
    cliente = cliente_http(superusuario)
    for url in ["/v8/", "/v8/demo/clientes/", "/v8/demo/clientes/1/", "/v8/demo/spa/x"]:
        assert cliente.get(url).status_code == 200, url
        assert cliente.head(url).status_code == 200, url
        for metodo in ("post", "put", "patch", "delete", "options"):
            assert getattr(cliente, metodo)(url).status_code == 405, (metodo, url)

    assert cliente.head(URL_DEMO_FRAGMENTO).status_code == 200
    for metodo in ("post", "put", "patch", "delete"):
        assert getattr(cliente, metodo)(URL_DEMO_FRAGMENTO).status_code == 405

    for classe in (views.PaginaV8View, views.FragmentoV8View, views.ZonaV8View):
        assert classe.http_method_names == ["get", "head"]


@pytest.mark.spec("V8-ARQ-067")
def test_cookie_de_preferencia_so_vale_com_valor_da_lista():
    padrao = {"tema": "oficial", "modo": None, "sidebar": "expandida"}
    assert s_global.preferencias({}) == padrao
    assert s_global.preferencias(None) == padrao
    assert s_global.preferencias(
        {"v8_tema": "tema2", "v8_modo": "escuro", "v8_sidebar": "recolhida"}
    ) == {"tema": "tema2", "modo": "escuro", "sidebar": "recolhida"}
    assert s_global.preferencias({"v8_modo": "claro"})["modo"] == "claro"
    for invalido in ["", "Escuro", "escuro ", "dark", "auto", '"><b>', "claro;x"]:
        lido = s_global.preferencias(
            {"v8_tema": invalido, "v8_modo": invalido, "v8_sidebar": invalido}
        )
        assert lido == padrao, invalido
    # Só os três cookies de preferência são lidos.
    assert (
        s_global.preferencias({"tema": "tema1", "modo": "escuro", "v8_outro": "x"})
        == padrao
    )


@pytest.mark.spec("V8-ARQ-068")
def test_subcaminho_da_zona_e_caminho_do_404_nao_sao_renderizados(superusuario):
    cliente = cliente_http(superusuario)
    base = html_de(cliente.get("/v8/demo/spa/"))
    for subcaminho in [
        "zzmarcadorzz/1",
        "../../base.html",
        "v8/erros/404.html",
        "%3Cb%3Ezzmarcadorzz",
    ]:
        resposta = cliente.get(f"/v8/demo/spa/{subcaminho}")
        html = html_de(resposta)
        assert resposta.status_code == 200, subcaminho
        assert "zzmarcadorzz" not in html
        # O subcaminho não muda a página entregue.
        limpar = lambda h: re.sub(r'name="csrfmiddlewaretoken" value="[^"]+"', "", h)
        assert limpar(html) == limpar(base)

    for caminho in [
        "/v8/zzmarcadorzz/",
        "/v8/%3Cb%3Ezzmarcadorzz",
        "/v8/demo/clientes/999/",
    ]:
        for cabecalhos in ({}, CABECALHOS_CLIENTE):
            resposta = cliente.get(caminho + "?zzmarcadorzz=1", headers=cabecalhos)
            assert resposta.status_code == 404, caminho
            assert "zzmarcadorzz" not in html_de(resposta)
            assert "999" not in html_de(resposta)


@pytest.mark.spec("V8-ARQ-069")
def test_pagina_publica_nao_dispara_tarefa_cara():
    # O app não usa fila, PDF, IA nem OCR.
    proibidos = ("celery", "tasks", ".delay(", "apply_async", "genia", "ocr", "pdf")
    for arquivo in sorted(DIR_APP.rglob("*.py")):
        if "tests" in arquivo.parts:
            continue
        fonte = arquivo.read_text(encoding="utf-8").lower()
        for termo in proibidos:
            assert termo not in fonte, (arquivo.name, termo)

    publicas = [
        r.name
        for r in cmj.v8.urls.urlpatterns
        if getattr(r.callback.view_class, "exige", None) is None
        and not hasattr(r.callback.view_class, "zona")
    ]
    # Além da capa e do 404, só as páginas do design system (ds.md, D1).
    do_ds = ["ds", "ds_temas"] + [f"ds_tema_{nome}" for nome in s_global.TEMAS]
    assert sorted(publicas) == sorted(["inicio", "nao_encontrado", *do_ds])
    assert cliente_http().get("/v8/").status_code == 200
