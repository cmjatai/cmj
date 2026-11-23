"""Testes da spec docs/specs/v8/templates.md.

Cada teste está ligado a uma regra pelo marker ``spec``.
"""

import dataclasses
import inspect
import re

import pytest
from django.conf import settings
from django.contrib import messages as niveis
from django.contrib.messages.storage.base import Message
from django.core.cache.utils import make_template_fragment_key
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode, IncludeNode

import cmj.v8.urls
from cmj.v8 import views
from cmj.v8.services import s_global, s_menu
from cmj.v8.tests.conftest import (
    DIR_CSS_OFICIAL,
    DIR_TEMPLATES_V8,
    URLS_DEMO_LAYOUTS,
    cliente_http,
    criar_usuario,
    html_de,
    ler_json_script,
    pagina_no_layout,
    renderizar,
    templates_v8,
    trecho,
)

pytestmark = pytest.mark.django_db

BASE = "base_v8.html"
SHELL = "v8/layouts/_shell.html"
LAYOUTS = ["landing", "app_topbar", "app_sidebar", "minimal"]
COM_SHELL = ["landing", "app_topbar", "app_sidebar"]
CONCRETOS = [f"v8/layouts/{nome}.html" for nome in LAYOUTS]
PAGINA_DA_ZONA = "v8/paginas/zona.html"

BLOCOS_DA_BASE = [
    "html_attrs",
    "title",
    "meta",
    "page_data",
    "assets",
    "body_class",
    "layout",
    "scripts",
]
# Blocks de `_shell.html`, na ordem em que aparecem no arquivo.
BLOCOS_DO_SHELL = [
    "layout",
    "sprite",
    "skiplink",
    "layout_name",
    "header",
    "header_start",
    "brand",
    "header_nav",
    "header_actions",
    "user",
    "aside",
    "breadcrumbs",
    "hero",
    "messages",
    "content",
    "footer",
]
# Regiões que uma página pode preencher, na ordem em que saem no HTML.
REGIOES = [
    "header_start",
    "brand",
    "header_nav",
    "header_actions",
    "user",
    "aside",
    "breadcrumbs",
    "hero",
    "messages",
    "content",
    "footer",
]
TRILHA = {"v8": {"trilha": [("Início", "/v8/"), ("Página", None)]}}
SCRIPT_MAIN = r'<script[^>]*type="module"[^>]*src="[^"]*main[^"]*\.js"'


def nomes():
    """Nome de cada template do v8, como o Django o carrega."""
    return [p.relative_to(DIR_TEMPLATES_V8).as_posix() for p in templates_v8()]


def paginas():
    """Templates do nível 3: tudo o que não é base, layout, parcial do shell nem fragmento."""
    fora = ("v8/layouts/", "v8/shell/", "v8/partials/")
    return [n for n in nomes() if n != BASE and not n.startswith(fora)]


def fonte_de(nome):
    return (DIR_TEMPLATES_V8 / nome).read_text(encoding="utf-8")


def arvore(nome):
    return get_template(nome).template.nodelist


def pai(nome):
    """Nome do template estendido, a variável usada no ``extends`` ou ``None``."""
    nos = arvore(nome).get_nodes_by_type(ExtendsNode)
    if not nos:
        return None
    expressao = nos[0].parent_name
    return expressao.var if isinstance(expressao.var, str) else expressao.token


def blocos(nome):
    return [no.name for no in arvore(nome).get_nodes_by_type(BlockNode)]


def includes_fora_de_block(nodelist, em_block=False):
    """Nomes dos templates incluídos fora de qualquer ``{% block %}``."""
    achados = []
    for no in nodelist:
        if isinstance(no, IncludeNode) and not em_block:
            achados.append(no.template.token)
        dentro = em_block or isinstance(no, BlockNode)
        for atributo in getattr(no, "child_nodelists", ()):
            filhos = getattr(no, atributo, None)
            if filhos is not None:
                achados += includes_fora_de_block(filhos, dentro)
    return achados


def marcas(regioes):
    """Blocks que escrevem ``[nome]`` em cada região."""
    return "".join(f"{{% block {r} %}}[{r}]{{% endblock %}}" for r in regioes)


def menu_de(html):
    return trecho(html, '<nav id="v8-menu-principal"', "</nav>")


def templates_usados(resposta):
    return [t.name for t in resposta.templates]


# --- Camadas -----------------------------------------------------------------------


@pytest.mark.spec("V8-TPL-001")
def test_heranca_tem_um_sentido_so():
    camada = {BASE: 0, SHELL: 1}
    camada.update({nome: 2 for nome in CONCRETOS})
    camada.update({nome: 3 for nome in paginas()})

    assert pai(BASE) is None
    for nome, nivel in camada.items():
        if nome in (BASE, PAGINA_DA_ZONA):
            continue
        # Todo template estende um de camada acima, nunca da mesma nem de baixo.
        assert camada[pai(nome)] < nivel, nome
    # A zona estende o layout que a view informa: sempre um dos concretos.
    assert pai(PAGINA_DA_ZONA) == "v8_layout_zona"
    assert sorted(s_global.LAYOUTS.values()) == sorted(CONCRETOS)


@pytest.mark.spec("V8-TPL-002")
def test_ha_quatro_layouts_concretos():
    em_disco = sorted(n for n in nomes() if n.startswith("v8/layouts/"))
    assert em_disco == sorted(CONCRETOS + [SHELL])

    assert pai(SHELL) == BASE
    assert pai("v8/layouts/landing.html") == SHELL
    assert pai("v8/layouts/app_topbar.html") == SHELL
    assert pai("v8/layouts/app_sidebar.html") == SHELL
    assert pai("v8/layouts/minimal.html") == BASE
    assert list(s_global.LAYOUTS) == LAYOUTS


@pytest.mark.spec("V8-TPL-003")
def test_layout_abstrato_nao_e_estendido_por_pagina_nem_renderizado_por_view(
    superusuario,
):
    abstratos = [n for n in nomes() if n.rsplit("/", 1)[-1].startswith("_")]
    assert abstratos == [SHELL]
    for nome in paginas():
        assert pai(nome) not in abstratos + [BASE], nome

    # Nenhuma view cita um layout ou a base: o que elas renderizam são páginas.
    fonte = inspect.getsource(views)
    assert "v8/layouts/" not in fonte and BASE not in fonte
    cliente = cliente_http(superusuario)
    for url in ["/v8/", "/v8/demo/clientes/", "/v8/demo/spa/", "/v8/nao-existe/"]:
        primeiro = templates_usados(cliente.get(url))[0]
        assert primeiro in paginas(), url


# --- Nível 1: base ------------------------------------------------------------------


@pytest.mark.spec("V8-TPL-010")
def test_base_so_tem_o_esqueleto_do_documento():
    html = renderizar(f'{{% extends "{BASE}" %}}')
    assert html.startswith("<!DOCTYPE html>")
    for marco in ("<html", "<head>", "</head>", "<body", "</body>", "</html>"):
        assert html.count(marco) == 1, marco

    corpo = re.search(r"<body[^>]*>(.*)</body>", html, re.S).group(1)
    assert corpo.split() == ["<div", 'id="cmj-v8-app"></div>']
    for visual in ("<header", "<nav", "<main", "<aside", "<footer", "<svg", "<a "):
        assert visual not in html, visual


@pytest.mark.spec("V8-TPL-011")
def test_blocos_da_base_sao_exatamente_os_previstos():
    assert blocos(BASE) == BLOCOS_DA_BASE


@pytest.mark.spec("V8-TPL-012")
def test_o_essencial_fica_fora_de_block_e_chega_a_toda_pagina():
    vazios = "".join(f"{{% block {b} %}}{{% endblock %}}" for b in BLOCOS_DA_BASE)
    html = renderizar(f'{{% extends "{BASE}" %}}{vazios}')

    assert '<meta charset="utf-8">' in html
    assert '<meta name="viewport"' in html
    assert '<link rel="icon"' in html
    assert ler_json_script(html, "v8-global")["autenticado"] is False
    assert ler_json_script(html, "v8-messages") == []
    assert re.search(SCRIPT_MAIN, html)
    if settings.DJANGO_VITE["v8"]["dev_mode"]:
        assert "@vite/client" in html
    assert '<div id="cmj-v8-app"></div>' in html

    # Na fonte, nada disso está dentro de um block.
    fora = re.sub(r"{% block \w+ %}.*?{% endblock %}", "", fonte_de(BASE), flags=re.S)
    for essencial in (
        'charset="utf-8"',
        'name="viewport"',
        'rel="icon"',
        "{% v8_dados_globais %}",
        "{% v8_mensagens %}",
        "{% vite_hmr_client app='v8' %}",
        "{% vite_asset 'main.js' app='v8' %}",
        '<div id="cmj-v8-app"></div>',
    ):
        assert essencial in fora, essencial


@pytest.mark.spec("V8-TPL-013")
def test_base_emite_em_html_so_lang_tema_e_modo():
    for layout in LAYOUTS:
        sem_cookie = pagina_no_layout(layout)
        com_modo = pagina_no_layout(
            layout, cookies={"v8_modo": "escuro", "v8_sidebar": "recolhida"}
        )
        if layout == "app_sidebar":
            assert (
                '<html lang="pt-br" data-tema="oficial" data-sidebar="expandida">'
                in sem_cookie
            )
            assert (
                '<html lang="pt-br" data-tema="oficial" data-modo="escuro" data-sidebar="recolhida">'
                in com_modo
            )
        else:
            assert '<html lang="pt-br" data-tema="oficial">' in sem_cookie, layout
            assert (
                '<html lang="pt-br" data-tema="oficial" data-modo="escuro">' in com_modo
            ), layout

    assert '<html lang="pt-br" data-tema="oficial">' in renderizar(
        f'{{% extends "{BASE}" %}}'
    )
    # O atributo a mais entra pelo block, e só por ele.
    html = renderizar(
        f'{{% extends "{BASE}" %}}{{% block html_attrs %}} data-zz="1"{{% endblock %}}'
    )
    assert '<html lang="pt-br" data-tema="oficial" data-zz="1">' in html


@pytest.mark.spec("V8-TPL-014")
@pytest.mark.parametrize("layout", LAYOUTS)
def test_titulo_padrao_vem_da_base(layout):
    com_titulo = pagina_no_layout(layout, contexto={"v8": {"titulo": "Relatórios"}})
    assert "<title>Relatórios · PortalCMJ</title>" in com_titulo
    assert "<title>PortalCMJ</title>" in pagina_no_layout(layout)

    # Os layouts não repetem a regra.
    assert "title" not in blocos(f"v8/layouts/{layout}.html")
    assert "title" not in blocos(SHELL)
    assert "v8.titulo" not in fonte_de(f"v8/layouts/{layout}.html")


@pytest.mark.spec("V8-TPL-015")
def test_meta_assets_e_scripts_nascem_vazios_e_tem_lugar_certo():
    padrao = renderizar(f'{{% extends "{BASE}" %}}')
    vazios = renderizar(
        f'{{% extends "{BASE}" %}}{{% block meta %}}{{% endblock %}}'
        "{% block assets %}{% endblock %}{% block scripts %}{% endblock %}"
    )
    assert padrao == vazios

    html = renderizar(
        f'{{% extends "{BASE}" %}}'
        '{% block meta %}<meta name="description" content="zzmeta">{% endblock %}'
        '{% block assets %}<link rel="stylesheet" href="/zzassets.css">{% endblock %}'
        '{% block scripts %}<span id="zzscripts"></span>{% endblock %}'
    )
    cabeca = html[: html.index("</head>")]
    assert "zzmeta" in cabeca and "zzassets" in cabeca
    assert cabeca.index("</title>") < cabeca.index("zzmeta")
    assert re.search(SCRIPT_MAIN, cabeca).start() < cabeca.index("zzassets")
    assert (
        html.index('<div id="cmj-v8-app"></div>')
        < html.index("zzscripts")
        < html.index("</body>")
    )


@pytest.mark.spec("V8-TPL-016")
def test_base_nao_tem_include_cache_menu_nem_usuario():
    fonte = fonte_de(BASE)
    for proibido in ("{% include", "{% cache", "v8_menu", "v8_usuario", "csrf_token"):
        assert proibido not in fonte, proibido
    # Do contexto, só o título. Tema e modo vêm da tag de preferências.
    assert sorted(set(re.findall(r"{{\s*([\w.]+)", fonte))) == [
        "v8.titulo",
        "v8_pref.modo",
        "v8_pref.tema",
    ]
    assert "v8_pref.sidebar" not in fonte


# --- Nível 2: shell abstrato ---------------------------------------------------------


@pytest.mark.spec("V8-TPL-020")
def test_shell_abstrato_define_as_regioes_em_blocks_e_em_ordem():
    assert blocos(SHELL) == BLOCOS_DO_SHELL

    html = renderizar(f'{{% extends "{SHELL}" %}}' + marcas(REGIOES))
    posicoes = [html.index(f"[{regiao}]") for regiao in REGIOES]
    assert posicoes == sorted(posicoes)
    # O cabeçalho envolve as cinco primeiras regiões, e o <main>, as quatro do miolo.
    assert (
        html.index('<header class="v8-topbar">')
        < html.index("[header_start]")
        < html.index("[user]")
        < html.index("</header>")
        < html.index("[aside]")
        < html.index('<main id="conteudo"')
        < html.index("[breadcrumbs]")
        < html.index("[content]")
        < html.index("</main>")
        < html.index("[footer]")
    )


@pytest.mark.spec("V8-TPL-021")
def test_conteudo_padrao_do_shell_e_escrito_uma_unica_vez():
    mensagem = Message(niveis.SUCCESS, "Feito.")
    html = renderizar(
        f'{{% extends "{SHELL}" %}}', contexto={**TRILHA, "messages": [mensagem]}
    )
    for padrao in (
        '<svg class="v8-icones"',
        '<a class="v8-pular" href="#conteudo">Ir para o conteúdo</a>',
        '<a class="v8-topbar-marca" href="/v8/">PortalCMJ</a>',
        'data-v8-acao="modo"',
        '<div class="v8-usuario">',
        '<nav class="v8-trilha" aria-label="Trilha">',
        '<p class="v8-alerta v8-alerta-sucesso">Feito.</p>',
    ):
        assert padrao in html, padrao

    # Nascem vazios: sem botão antes da marca, sem menu, aside, hero nem rodapé.
    for ausente in (
        "<aside",
        "<footer",
        "v8-menu",
        "v8-hero",
        'data-v8-acao="sidebar"',
    ):
        assert ausente not in html, ausente
    assert 'data-v8-acao="menu"' not in html
    cabecalho = trecho(html, '<header class="v8-topbar">', "</header>")
    assert cabecalho.split(">", 1)[1].lstrip().startswith('<a class="v8-topbar-marca"')
    assert re.search(
        r'<div class="v8-conteudo">\s*<noscript>.*?</noscript>\s*</div>', html, re.S
    )

    # Cada parte comum está num arquivo só.
    for marca in (
        "v8-pular",
        "v8-topbar-marca",
        'data-v8-acao="modo"',
        "v8-usuario",
        "v8-trilha",
    ):
        donos = [nome for nome in nomes() if marca in fonte_de(nome)]
        assert donos == [SHELL], marca


@pytest.mark.spec("V8-TPL-022")
def test_layouts_com_shell_so_sobrescrevem_regioes_na_mesma_ordem():
    saidas = {}
    for layout in COM_SHELL:
        definidos = blocos(f"v8/layouts/{layout}.html")
        assert "layout" not in definidos, layout
        assert "header" not in definidos, layout

        html = pagina_no_layout(layout, marcas(REGIOES))
        posicoes = [html.index(f"[{regiao}]") for regiao in REGIOES]
        assert posicoes == sorted(posicoes), layout
        saidas[layout] = re.sub(r'data-v8-layout="\w+"', "", html)

    # Com as mesmas regiões preenchidas, só o atributo de <html> distingue os três.
    sem_sidebar = saidas["app_sidebar"].replace(' data-sidebar="expandida"', "")
    assert saidas["landing"] == saidas["app_topbar"] == sem_sidebar


@pytest.mark.spec("V8-TPL-023")
@pytest.mark.parametrize("layout", COM_SHELL)
def test_layout_com_shell_tem_um_main_entre_as_docas(layout):
    html = pagina_no_layout(layout)
    assert html.count("<main") == 1
    assert html.count("data-v8-doca=") == 2
    assert (
        html.index('<div class="v8-doca" data-v8-doca="left"></div>')
        < html.index('<main id="conteudo" class="v8-main" tabindex="-1">')
        < html.index("</main>")
        < html.index('<div class="v8-doca" data-v8-doca="right"></div>')
    )


@pytest.mark.spec("V8-TPL-024")
def test_elemento_raiz_do_layout_informa_o_nome():
    for layout in COM_SHELL:
        html = pagina_no_layout(layout)
        assert f'<div class="v8-shell" data-v8-layout="{layout}">' in html
        assert html.count("data-v8-layout=") == 1
    minimal = pagina_no_layout("minimal")
    assert '<main id="conteudo" class="v8-nua" data-v8-layout="minimal">' in minimal
    assert minimal.count("data-v8-layout=") == 1

    # CSS e JavaScript não usam outra marca de layout.
    css = (DIR_CSS_OFICIAL / "shell.css").read_text(encoding="utf-8")
    assert set(re.findall(r'data-v8-layout="(\w+)"', css)) <= set(LAYOUTS)
    assert "v8-layout-" not in css


# --- Layouts concretos ----------------------------------------------------------------


@pytest.mark.spec("V8-TPL-030")
def test_app_sidebar_tem_barra_lateral_botao_e_data_sidebar():
    html = pagina_no_layout("app_sidebar", cookies={"v8_sidebar": "recolhida"})
    assert '<html lang="pt-br" data-tema="oficial" data-sidebar="recolhida">' in html
    lateral = trecho(html, '<aside id="v8-sidebar" class="v8-sidebar">', "</aside>")
    assert '<nav id="v8-menu-principal" class="v8-menu"' in lateral

    cabecalho = trecho(html, '<header class="v8-topbar">', "</header>")
    assert (
        'data-v8-acao="sidebar" aria-controls="v8-sidebar" aria-expanded="false"'
        in cabecalho
    )
    assert cabecalho.index('data-v8-acao="sidebar"') < cabecalho.index(
        "v8-topbar-marca"
    )
    assert "v8-menu-principal" not in cabecalho
    assert 'data-v8-acao="menu"' not in html and "<footer" not in html


@pytest.mark.spec("V8-TPL-031")
def test_app_topbar_tem_menu_no_cabecalho_e_conteudo_centralizado():
    html = pagina_no_layout("app_topbar", contexto=TRILHA)
    cabecalho = trecho(html, '<header class="v8-topbar">', "</header>")
    assert '<nav id="v8-menu-principal" class="v8-menu"' in cabecalho
    assert cabecalho.index("v8-topbar-marca") < cabecalho.index('<nav id="v8-menu-')
    assert 'data-v8-acao="menu" aria-controls="v8-menu-principal"' in cabecalho
    assert cabecalho.index('data-v8-acao="menu"') < cabecalho.index("v8-topbar-marca")
    assert '<nav class="v8-trilha"' in html

    for ausente in ("<aside", "data-sidebar", 'data-v8-acao="sidebar"', "<footer"):
        assert ausente not in html, ausente

    # A largura máxima do conteúdo é um token.
    tokens = (DIR_CSS_OFICIAL / "tokens.css").read_text(encoding="utf-8")
    css = (DIR_CSS_OFICIAL / "shell.css").read_text(encoding="utf-8")
    assert re.search(r"--largura-conteudo:\s*[\d.]+rem;", tokens)
    regra = re.search(r'\[data-v8-layout="app_topbar"\] \.v8-conteudo[^{]*{[^}]*}', css)
    assert "max-width: var(--largura-conteudo);" in regra.group(0)


@pytest.mark.spec("V8-TPL-032")
def test_landing_tem_menu_hero_de_largura_total_e_rodape():
    html = pagina_no_layout(
        "landing",
        '{% block hero %}<section class="v8-hero">[hero]</section>{% endblock %}'
        "{% block content %}[content]{% endblock %}"
        "{% block footer_nav %}[footer_nav]{% endblock %}"
        "{% block footer_info %}[footer_info]{% endblock %}",
        contexto=TRILHA,
    )
    cabecalho = trecho(html, '<header class="v8-topbar">', "</header>")
    assert '<nav id="v8-menu-principal" class="v8-menu"' in cabecalho
    assert 'data-v8-acao="menu"' in cabecalho

    # O hero fica no <main>, antes e fora da coluna de conteúdo.
    assert (
        html.index('<main id="conteudo"')
        < html.index("[hero]")
        < html.index('<div class="v8-conteudo">')
        < html.index("[content]")
        < html.index("</main>")
    )
    rodape = trecho(html, '<footer class="v8-rodape">', "</footer>")
    assert rodape.index("PortalCMJ") < rodape.index("[footer_nav]")
    assert rodape.index("[footer_nav]") < rodape.index("[footer_info]")
    assert html.index("</main>") < html.index('<footer class="v8-rodape">')

    for ausente in ("<aside", "v8-trilha", "data-sidebar", 'data-v8-acao="sidebar"'):
        assert ausente not in html, ausente

    # Sem a página preencher: hero vazio e rodapé só com a marca e uma linha neutra.
    padrao = pagina_no_layout("landing")
    assert "v8-hero" not in padrao
    rodape = trecho(padrao, '<footer class="v8-rodape">', "</footer>")
    texto = " ".join(re.sub(r"<[^>]+>", " ", rodape).split())
    assert texto == "PortalCMJ Portal da Câmara Municipal de Jataí"


@pytest.mark.spec("V8-TPL-033")
def test_minimal_so_tem_o_main_com_mensagens_e_conteudo():
    html = pagina_no_layout(
        "minimal",
        "{% block content %}[content]{% endblock %}",
        contexto={**TRILHA, "messages": [Message(niveis.WARNING, "Atenção.")]},
    )
    corpo = re.search(r"<body[^>]*>(.*)</body>", html, re.S).group(1)
    assert corpo.count("<main") == 1
    principal = trecho(corpo, "<main", "</main>")
    assert '<p class="v8-alerta v8-alerta-aviso">Atenção.</p>' in principal
    assert principal.index("v8-alerta-aviso") < principal.index("[content]")

    for ausente in ("<header", "<nav", "<aside", "<footer", "v8-shell", "data-v8-doca"):
        assert ausente not in corpo, ausente
    fora = corpo.replace(principal, "").split()
    assert fora == ["<div", 'id="cmj-v8-app"></div>']
    assert blocos("v8/layouts/minimal.html") == ["layout", "messages", "content"]


@pytest.mark.spec("V8-TPL-034")
@pytest.mark.parametrize("layout", LAYOUTS)
def test_pagina_que_so_preenche_content_renderiza_em_qualquer_layout(layout, comum):
    definidos = blocos(f"v8/layouts/{layout}.html") + blocos(
        pai(f"v8/layouts/{layout}.html")
    )
    assert "content" in definidos and "messages" in definidos

    blocos_da_pagina = "{% block content %}<p>só o conteúdo</p>{% endblock %}"
    for usuario in (None, comum):
        html = pagina_no_layout(layout, blocos_da_pagina, usuario=usuario)
        assert "<p>só o conteúdo</p>" in html
        assert ler_json_script(html, "v8-global")["autenticado"] is (
            usuario is not None
        )
        assert ler_json_script(html, "v8-messages") == []
        assert '<div id="cmj-v8-app"></div>' in html
        assert "<noscript>" not in html

    com_mensagem = pagina_no_layout(
        layout,
        blocos_da_pagina,
        contexto={"messages": [Message(niveis.ERROR, "Falhou.")]},
    )
    assert re.search(
        r'<noscript>\s*<p class="v8-alerta v8-alerta-erro">Falhou.</p>\s*</noscript>',
        com_mensagem,
    )
    sem_o_bloco = pagina_no_layout(
        layout,
        blocos_da_pagina + "{% block messages %}{% endblock %}",
        contexto={"messages": [Message(niveis.ERROR, "Falhou.")]},
    )
    assert "<noscript>" not in sem_o_bloco


# --- Includes -------------------------------------------------------------------------


@pytest.mark.spec("V8-TPL-040")
def test_em_layout_e_em_pagina_todo_include_fica_dentro_de_block():
    conferidos = [SHELL] + CONCRETOS + paginas()
    for nome in conferidos:
        assert includes_fora_de_block(arvore(nome)) == [], nome
    assert "{% include" not in fonte_de(BASE)

    # Trocar o block tira o include da página.
    html = pagina_no_layout("app_sidebar", "{% block menu %}[menu]{% endblock %}")
    assert "[menu]" in html and "v8-menu-principal" not in html
    html = pagina_no_layout("app_topbar", "{% block sprite %}{% endblock %}")
    assert '<svg class="v8-icones"' not in html


@pytest.mark.spec("V8-TPL-041")
def test_parciais_do_shell_sao_sprite_menu_e_mensagens():
    parciais = sorted(n for n in nomes() if n.startswith("v8/shell/"))
    assert parciais == [
        "v8/shell/icones.html",
        "v8/shell/mensagens.html",
        "v8/shell/menu.html",
        "v8/shell/menu_itens.html",
    ]
    for nome in parciais:
        assert pai(nome) is None, nome

    def incluidos(nome):
        return sorted(re.findall(r'{% include "([^"]+)"', fonte_de(nome)))

    assert incluidos(SHELL) == ["v8/shell/icones.html", "v8/shell/mensagens.html"]
    assert incluidos("v8/layouts/minimal.html") == ["v8/shell/mensagens.html"]
    for layout in COM_SHELL:
        assert incluidos(f"v8/layouts/{layout}.html") == ["v8/shell/menu.html"]
    # O menu ocupa dois arquivos: o do cache e o da recursão dos itens.
    assert incluidos("v8/shell/menu.html") == ["v8/shell/menu_itens.html"]
    assert incluidos("v8/shell/menu_itens.html") == ["v8/shell/menu_itens.html"]


@pytest.mark.spec("V8-TPL-042")
def test_os_tres_layouts_usam_o_mesmo_menu_e_a_mesma_entrada_de_cache(
    cache_real, superusuario, monkeypatch
):
    ativo = {"v8": {"menu_ativo": "demo-clientes"}}
    chave = make_template_fragment_key(
        "v8_menu",
        [s_menu.VERSAO_MENU, s_global.hash_permissoes(superusuario), "demo-clientes"],
    )
    assert cache_real.get(chave) is None

    primeiro = menu_de(
        pagina_no_layout("app_sidebar", usuario=superusuario, contexto=ativo)
    )
    em_cache = cache_real.get(chave)
    assert em_cache and em_cache.strip() in primeiro
    assert 'aria-current="page"' in primeiro

    # Os outros dois não montam o menu de novo: usam a entrada que já existe.
    def nao_deveria_montar(*args, **kwargs):
        raise AssertionError("o menu foi montado de novo")

    monkeypatch.setattr(s_menu, "menu_para", nao_deveria_montar)
    for layout in ("app_topbar", "landing"):
        html = pagina_no_layout(layout, usuario=superusuario, contexto=ativo)
        assert menu_de(html) == primeiro, layout


# --- Nível 3: páginas ---------------------------------------------------------------


@pytest.mark.spec("V8-TPL-050")
def test_toda_pagina_estende_um_layout_concreto():
    assert len(paginas()) >= 10
    for nome in paginas():
        if nome == PAGINA_DA_ZONA:
            continue
        assert pai(nome) in CONCRETOS, nome
    for layout in LAYOUTS:
        assert pai(f"v8/demo/layouts/{layout}.html") == f"v8/layouts/{layout}.html"


@pytest.mark.spec("V8-TPL-051")
def test_pagina_nao_sobrescreve_layout_nem_html_attrs():
    proibidos = {"layout", "html_attrs", "layout_name"}
    for nome in paginas():
        assert not proibidos & set(blocos(nome)), nome


@pytest.mark.spec("V8-TPL-052")
def test_zona_e_uma_pagina_no_layout_que_a_zona_declara(superusuario, monkeypatch):
    zona = s_global.ZONAS["demo-spa"]
    assert zona.layout == "app_sidebar" == s_global.LAYOUT_PADRAO
    assert s_global.Zona("x", "x", "X").layout == "app_sidebar"
    assert blocos(PAGINA_DA_ZONA) == ["content"]

    cliente = cliente_http(superusuario)
    resposta = cliente.get("/v8/demo/spa/clientes/3")
    usados = templates_usados(resposta)
    assert usados[0] == PAGINA_DA_ZONA
    assert "v8/layouts/app_sidebar.html" in usados
    html = html_de(resposta)
    conteudo = html[html.index('<div class="v8-conteudo">') :]
    assert '<div class="v8-zona" data-vue-zone="demo-spa">' in conteudo

    monkeypatch.setitem(
        s_global.ZONAS, "demo-spa", dataclasses.replace(zona, layout="app_topbar")
    )
    resposta = cliente.get("/v8/demo/spa/")
    usados = templates_usados(resposta)
    assert "v8/layouts/app_topbar.html" in usados
    assert "v8/layouts/app_sidebar.html" not in usados
    html = html_de(resposta)
    assert '<div class="v8-shell" data-v8-layout="app_topbar">' in html
    assert '<div class="v8-zona" data-vue-zone="demo-spa">' in html


@pytest.mark.spec("V8-TPL-053")
def test_cada_pagina_existente_usa_o_layout_previsto(comum, superusuario):
    def layout_de(resposta):
        usados = [n for n in templates_usados(resposta) if n in CONCRETOS]
        assert len(usados) == 1
        return usados[0].rsplit("/", 1)[-1].removesuffix(".html")

    assert layout_de(cliente_http().get("/v8/")) == "landing"
    cliente = cliente_http(superusuario)
    assert layout_de(cliente.get("/v8/demo/clientes/")) == "app_sidebar"
    assert layout_de(cliente.get("/v8/demo/clientes/1/")) == "app_sidebar"
    assert layout_de(cliente.get("/v8/demo/spa/")) == "app_sidebar"
    assert layout_de(cliente.get("/v8/ds/")) == "app_sidebar"
    assert layout_de(cliente.get("/v8/ds/temas/")) == "app_sidebar"
    assert layout_de(cliente.get("/v8/ds/temas/verde/")) == "app_sidebar"
    assert layout_de(cliente.get("/v8/nao-existe/")) == "minimal"
    assert layout_de(cliente_http(comum).get("/v8/demo/clientes/")) == "minimal"


@pytest.mark.spec("V8-TPL-054")
def test_fragmentos_nao_entram_na_heranca():
    fragmentos = [n for n in nomes() if n.startswith("v8/partials/")]
    assert fragmentos
    for nome in fragmentos:
        assert pai(nome) is None, nome
        assert blocos(nome) == [], nome


# --- Requisitos de segurança ------------------------------------------------------------


@pytest.mark.spec("V8-TPL-060")
def test_layout_nunca_vem_da_requisicao(superusuario):
    # Nas páginas o nome do layout está escrito no extends.
    for nome in paginas():
        fonte = fonte_de(nome)
        if nome == PAGINA_DA_ZONA:
            assert fonte.startswith("{% extends v8_layout_zona %}")
        else:
            assert re.match(r'{% extends "v8/layouts/\w+\.html" %}', fonte), nome

    # A zona só aceita um dos quatro nomes, e o erro aparece na declaração.
    for invalido in ("outro", "", "_shell", "v8/layouts/minimal.html", "../base_v8"):
        with pytest.raises(ValueError):
            s_global.Zona("x", "x", "X", layout=invalido)

    # Query string, cookie e cabeçalho não mudam o layout entregue.
    cliente = cliente_http(superusuario)
    hostil = cliente_http(superusuario)
    hostil.cookies["layout"] = "minimal"
    hostil.cookies["v8_layout_zona"] = "v8/layouts/minimal.html"
    query = "?layout=minimal&v8_layout_zona=v8/layouts/minimal.html"
    cabecalhos = {"X-Layout": "minimal", "X-V8-Layout-Zona": "v8/layouts/minimal.html"}
    for url in ["/v8/", "/v8/demo/clientes/", "/v8/demo/spa/", URLS_DEMO_LAYOUTS[1]]:
        esperado = templates_usados(cliente.get(url))
        assert templates_usados(hostil.get(url + query, headers=cabecalhos)) == esperado

    # O caminho escolhe a página de demonstração só entre as rotas declaradas.
    assert cliente.get("/v8/demo/layouts/_shell/").status_code == 404
    assert cliente.get("/v8/demo/layouts/outro/").status_code == 404


@pytest.mark.spec("V8-TPL-061")
def test_json_globais_e_csrf_ficam_fora_de_cache_e_de_block():
    for nome in nomes():
        fonte = fonte_de(nome)
        em_cache = "".join(re.findall(r"{% cache .*?{% endcache %}", fonte, re.S))
        for proprio in ("v8_dados_globais", "v8_mensagens", "csrf_token", "v8_usuario"):
            assert proprio not in em_cache, (nome, proprio)
        if nome != BASE:
            assert "v8_dados_globais" not in fonte, nome
            assert "{% v8_mensagens" not in fonte, nome

    # Uma página que sobrescreve tudo o que pode ainda sai com os dois JSON.
    todos = sorted(set(BLOCOS_DA_BASE + BLOCOS_DO_SHELL))
    vazios = "".join(f"{{% block {b} %}}{{% endblock %}}" for b in todos)
    for layout in LAYOUTS:
        html = pagina_no_layout(layout, vazios)
        assert ler_json_script(html, "v8-global")["usuario"] is None
        assert ler_json_script(html, "v8-messages") == []


@pytest.mark.spec("V8-TPL-062")
def test_menu_em_cache_e_o_mesmo_nos_tres_layouts_e_nao_tem_dado_proprio(
    cache_real, comum, superusuario
):
    ativo = {"v8": {"menu_ativo": "inicio"}}

    def links(layout, usuario):
        html = pagina_no_layout(layout, usuario=usuario, contexto=ativo)
        return re.findall(r'<a class="v8-menu-link" href="([^"]+)"', menu_de(html))

    # Duas voltas: na segunda, todas as entradas já estão em cache.
    for _ in range(2):
        for layout in COM_SHELL:
            publicos = ["/v8/", "/v8/ds/", "/v8/ds/temas/"]
            assert links(layout, None) == publicos, layout
            assert links(layout, comum) == publicos, layout
            da_raiz = links(layout, superusuario)
            assert "/v8/demo/clientes/" in da_raiz and len(da_raiz) > 3, layout

    chave = make_template_fragment_key(
        "v8_menu",
        [s_menu.VERSAO_MENU, s_global.hash_permissoes(superusuario), "inicio"],
    )
    em_cache = cache_real.get(chave)
    assert "Demonstração" in em_cache
    for proprio in (
        "Sofia",
        superusuario.email,
        "csrf",
        "v8-usuario",
        "v8-avatar",
        "data-v8-layout",
        "v8-topbar",
        "v8-sidebar",
        "<form",
        "<script",
    ):
        assert proprio not in em_cache, proprio
    # Os nomes dos layouts só aparecem nos links das páginas de demonstração deles.
    sem_links = re.sub(r"<a [^>]*>.*?</a>", "", em_cache, flags=re.S)
    for layout in LAYOUTS:
        assert layout not in sem_links, layout


@pytest.mark.spec("V8-TPL-063")
def test_meta_assets_e_scripts_nao_abrem_excecao_ao_escape():
    hostil = "\"><script>alert(1)</script><b x='"
    html = renderizar(
        f'{{% extends "{BASE}" %}}'
        '{% block meta %}<meta name="description" content="{{ texto }}">{% endblock %}'
        '{% block assets %}<link rel="prev" href="{{ texto }}">{% endblock %}'
        '{% block scripts %}<span title="{{ texto }}"></span>{% endblock %}',
        contexto={"texto": hostil},
    )
    assert "<script>alert(1)" not in html
    assert html.count("&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;") == 3
    assert html.count("</script>") == html.count("<script ")

    for arquivo in templates_v8():
        fonte = arquivo.read_text(encoding="utf-8")
        assert "<script" not in fonte, arquivo
        assert "|safe" not in fonte, arquivo
        assert "autoescape" not in fonte, arquivo
        assert not re.search(r"\son[a-z]+\s*=", fonte), arquivo

    # A base não monta endereço a partir do cabeçalho Host.
    fonte = fonte_de(BASE)
    for proibido in (
        "canonical",
        "og:url",
        "get_host",
        "build_absolute_uri",
        "HTTP_HOST",
    ):
        assert proibido not in fonte, proibido
    html = html_de(cliente_http().get("/v8/", headers={"Host": "zzhost.invalid"}))
    assert "zzhost" not in html


@pytest.mark.spec("V8-TPL-064")
def test_paginas_de_demonstracao_dos_layouts_exigem_superusuario(comum, superusuario):
    rotas = {
        r.name: r
        for r in cmj.v8.urls.urlpatterns
        if (r.name or "").startswith("demo_layout_")
    }
    assert sorted(rotas) == sorted(f"demo_layout_{nome}" for nome in LAYOUTS)
    for rota in rotas.values():
        classe = rota.callback.view_class
        assert classe is views.DemoLayoutView
        assert classe.exige == s_global.SUPERUSUARIO
        assert classe.http_method_names == ["get", "head"]

    for layout, url in zip(LAYOUTS, URLS_DEMO_LAYOUTS):
        anonimo = cliente_http().get(url)
        assert (
            anonimo.status_code == 302 and anonimo["Location"] == f"/login/?next={url}"
        )
        assert cliente_http(comum).get(url).status_code == 403

        cliente = cliente_http(superusuario)
        resposta = cliente.get(url + "?zzmarcadorzz=1")
        assert resposta.status_code == 200
        assert "private" in resposta["Cache-Control"]
        assert f"v8/layouts/{layout}.html" in templates_usados(resposta)
        html = html_de(resposta)
        assert f'data-v8-layout="{layout}"' in html
        # Só texto fixo: nada da requisição volta na página.
        assert "zzmarcadorzz" not in html
        assert cliente.head(url).status_code == 200
        for metodo in (cliente.post, cliente.put, cliente.delete):
            assert metodo(url).status_code == 405
