"""Testes da spec docs/specs/v8/shell.md.

Cada teste está ligado a uma regra pelo marker ``spec``.
"""

import re

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.cache.utils import make_template_fragment_key

from cmj.v8.services import s_global, s_menu
from cmj.v8.services.s_menu import ItemMenu
from cmj.v8.tests.conftest import (
    DIR_CSS_OFICIAL,
    cliente_http,
    criar_usuario,
    html_de,
    ler_json_script,
    pagina_no_layout,
    trecho,
)

pytestmark = pytest.mark.django_db


def menu_de(html):
    return trecho(html, '<nav id="v8-menu-principal"', "</nav>")


def topbar_de(html):
    return trecho(html, '<header class="v8-topbar">', "</header>")


def ids(itens):
    return [(item["id"], ids(item["filhos"])) for item in itens]


def permissao(n=0):
    """Uma permissão qualquer do banco e o nome dela em ``app.codename``."""
    perm = Permission.objects.select_related("content_type").order_by("pk")[n]
    return perm, f"{perm.content_type.app_label}.{perm.codename}"


def com_permissao(nome, *perms):
    usuario = criar_usuario(nome)
    usuario.user_permissions.add(*perms)
    return get_user_model().objects.get(pk=usuario.pk)


@pytest.fixture
def menu_de_teste(monkeypatch):
    """Árvore com os tipos de exigência: nenhuma, uma, lista e superusuário."""
    perm_a, nome_a = permissao(0)
    perm_b, nome_b = permissao(1)
    arvore = (
        ItemMenu("livre", "Livre", "/v8/", "casa"),
        ItemMenu("uma", "Exige A", "/v8/a/", permissao=nome_a),
        ItemMenu("lista", "Exige A ou B", "/v8/ab/", permissao=(nome_a, nome_b)),
        ItemMenu(
            "grupo",
            "Grupo",
            icone="grade",
            filhos=(
                ItemMenu("grupo-b", "Exige B", "/v8/b/", permissao=nome_b),
                ItemMenu(
                    "subgrupo",
                    "Subgrupo",
                    filhos=(
                        ItemMenu(
                            "raiz", "Só raiz", "/v8/r/", permissao=s_global.SUPERUSUARIO
                        ),
                    ),
                ),
            ),
        ),
    )
    monkeypatch.setattr(s_menu, "MENU", arvore)
    return {"a": perm_a, "b": perm_b}


# --- Menu ----------------------------------------------------------------------


@pytest.mark.spec("V8-SHELL-001")
def test_menu_e_uma_arvore_declarada_no_servico():
    def conferir(itens, vistos):
        for item in itens:
            assert isinstance(item, ItemMenu)
            assert item.id and item.rotulo
            assert item.id not in vistos
            vistos.add(item.id)
            assert isinstance(item.url, str) and isinstance(item.icone, str)
            assert item.permissao is None or isinstance(item.permissao, (str, tuple))
            assert isinstance(item.filhos, tuple)
            # Folha tem URL do v8, grupo tem filhos.
            assert item.filhos or item.url.startswith("/v8/")
            conferir(item.filhos, vistos)

    conferir(s_menu.MENU, set())
    assert isinstance(s_menu.VERSAO_MENU, int)
    with pytest.raises(AttributeError):
        s_menu.MENU[0].rotulo = "outro"


@pytest.mark.spec("V8-SHELL-002")
def test_menu_para_devolve_so_o_que_o_usuario_pode_ver(menu_de_teste, superusuario):
    livre = ("livre", [])
    assert ids(s_menu.menu_para(AnonymousUser())) == [livre]
    assert ids(s_menu.menu_para(criar_usuario("sem"))) == [livre]

    com_a = com_permissao("com.a", menu_de_teste["a"])
    assert ids(s_menu.menu_para(com_a)) == [livre, ("uma", []), ("lista", [])]

    # Na lista basta uma. O subgrupo, sem filho visível, some.
    com_b = com_permissao("com.b", menu_de_teste["b"])
    assert ids(s_menu.menu_para(com_b)) == [
        livre,
        ("lista", []),
        ("grupo", [("grupo-b", [])]),
    ]

    assert ids(s_menu.menu_para(superusuario)) == [
        livre,
        ("uma", []),
        ("lista", []),
        ("grupo", [("grupo-b", []), ("subgrupo", [("raiz", [])])]),
    ]

    item = s_menu.menu_para(AnonymousUser())[0]
    assert set(item) == {"id", "rotulo", "url", "icone", "ativo", "aberto", "filhos"}


@pytest.mark.spec("V8-SHELL-003")
def test_item_ativo_e_grupos_acima_dele_abertos(menu_de_teste, superusuario):
    def marcados(itens, chave):
        achados = []
        for item in itens:
            if item[chave]:
                achados.append(item["id"])
            achados += marcados(item["filhos"], chave)
        return achados

    menu = s_menu.menu_para(superusuario, "raiz")
    assert marcados(menu, "ativo") == ["raiz"]
    assert marcados(menu, "aberto") == ["grupo", "subgrupo"]

    menu = s_menu.menu_para(superusuario)
    assert marcados(menu, "ativo") == [] and marcados(menu, "aberto") == []
    menu = s_menu.menu_para(superusuario, "nao-existe")
    assert marcados(menu, "ativo") == [] and marcados(menu, "aberto") == []


@pytest.mark.spec("V8-SHELL-003")
def test_html_do_menu_marca_o_ativo_e_abre_o_grupo(superusuario):
    cliente = cliente_http(superusuario)

    menu = menu_de(html_de(cliente.get("/v8/demo/clientes/")))
    assert menu.count('aria-current="page"') == 1
    assert (
        '<a class="v8-menu-link" href="/v8/demo/clientes/" aria-current="page">' in menu
    )
    assert '<details class="v8-menu-grupo" open>' in menu

    menu = menu_de(html_de(cliente.get("/v8/demo/spa/clientes/3")))
    assert '<a class="v8-menu-link" href="/v8/demo/spa/" aria-current="page">' in menu
    assert '<details class="v8-menu-grupo" open>' in menu

    menu = menu_de(html_de(cliente.get("/v8/")))
    assert '<a class="v8-menu-link" href="/v8/" aria-current="page">' in menu
    assert menu.count('aria-current="page"') == 1
    assert '<details class="v8-menu-grupo">' in menu


@pytest.mark.spec("V8-SHELL-004")
@pytest.mark.spec("V8-DS-012")
def test_menu_inicial_tem_inicio_e_demonstracao_so_para_superusuario(
    comum, superusuario
):
    publico = [("inicio", []), ("ds", [("ds-vitrine", []), ("ds-temas", [])])]
    assert ids(s_menu.menu_para(AnonymousUser())) == publico
    assert ids(s_menu.menu_para(comum)) == publico
    menu = s_menu.menu_para(superusuario)
    assert ids(menu) == [
        ("inicio", []),
        (
            "demo",
            [
                ("demo-clientes", []),
                ("demo-spa", []),
                ("demo-layout-landing", []),
                ("demo-layout-app_topbar", []),
                ("demo-layout-app_sidebar", []),
                ("demo-layout-minimal", []),
            ],
        ),
        ("ds", [("ds-vitrine", []), ("ds-temas", [])]),
    ]
    assert [(i["rotulo"], i["url"], i["icone"]) for i in menu] == [
        ("Início", "/v8/", "casa"),
        ("Demonstração", "", "grade"),
        ("Design system", "", "paleta"),
    ]
    assert [(f["rotulo"], f["url"]) for f in menu[2]["filhos"]] == [
        ("Vitrine", "/v8/ds/"),
        ("Temas", "/v8/ds/temas/"),
    ]
    assert [(f["rotulo"], f["url"]) for f in menu[1]["filhos"]] == [
        ("Clientes (página com ilhas)", "/v8/demo/clientes/"),
        ("Clientes (zona SPA)", "/v8/demo/spa/"),
        ("Layout landing", "/v8/demo/layouts/landing/"),
        ("Layout app_topbar", "/v8/demo/layouts/app_topbar/"),
        ("Layout app_sidebar", "/v8/demo/layouts/app_sidebar/"),
        ("Layout minimal", "/v8/demo/layouts/minimal/"),
    ]


# --- Cache do menu ----------------------------------------------------------------


@pytest.mark.spec("V8-SHELL-010")
def test_cache_do_menu_tem_versao_permissoes_e_ativo_na_chave(
    cache_real, comum, superusuario
):
    outro_comum = criar_usuario("outro.comum", first_name="Outro")
    assert s_global.hash_permissoes(comum) == s_global.hash_permissoes(outro_comum)
    assert s_global.hash_permissoes(comum) != s_global.hash_permissoes(superusuario)

    def chave(usuario, ativo, versao=s_menu.VERSAO_MENU):
        return make_template_fragment_key(
            "v8_menu", [versao, s_global.hash_permissoes(usuario), ativo]
        )

    assert cache_real.get(chave(comum, "inicio")) is None
    html = html_de(cliente_http(comum).get("/v8/"))
    em_cache = cache_real.get(chave(comum, "inicio"))
    assert em_cache is not None
    assert em_cache.strip() in html
    # Mesmas permissões, mesma entrada.
    assert chave(outro_comum, "inicio") == chave(comum, "inicio")
    assert em_cache.strip() in html_de(cliente_http(outro_comum).get("/v8/"))

    # Outras permissões, outro item ativo ou outra versão: outra entrada.
    assert cache_real.get(chave(superusuario, "inicio")) is None
    cliente_http(superusuario).get("/v8/")
    cliente_http(superusuario).get("/v8/demo/clientes/")
    da_raiz = cache_real.get(chave(superusuario, "inicio"))
    da_raiz_na_demo = cache_real.get(chave(superusuario, "demo-clientes"))
    assert da_raiz and da_raiz_na_demo
    assert len({em_cache, da_raiz, da_raiz_na_demo}) == 3
    assert chave(comum, "inicio", versao=s_menu.VERSAO_MENU + 1) != chave(
        comum, "inicio"
    )


@pytest.mark.spec("V8-SHELL-011")
def test_mudanca_de_permissao_aparece_na_requisicao_seguinte(cache_real, menu_de_teste):
    usuario = criar_usuario("muda")
    cliente = cliente_http(usuario)

    menu = menu_de(html_de(cliente.get("/v8/")))
    assert "Exige A" not in menu and "Só raiz" not in menu

    usuario.user_permissions.add(menu_de_teste["a"])
    menu = menu_de(html_de(cliente.get("/v8/")))
    assert 'href="/v8/a/"' in menu and 'href="/v8/ab/"' in menu
    assert "Exige B" not in menu and "Só raiz" not in menu

    usuario.user_permissions.remove(menu_de_teste["a"])
    menu = menu_de(html_de(cliente.get("/v8/")))
    assert "Exige A" not in menu

    get_user_model().objects.filter(pk=usuario.pk).update(is_superuser=True)
    menu = menu_de(html_de(cliente.get("/v8/")))
    assert 'href="/v8/b/"' in menu and 'href="/v8/r/"' in menu


@pytest.mark.spec("V8-SHELL-012")
def test_trecho_em_cache_nao_tem_dado_proprio_de_usuario(cache_real, superusuario):
    cliente = cliente_http(superusuario)
    cliente.post("/v8/demo/clientes/arquivar/", {"ids": ["1"]})
    html = html_de(cliente.get("/v8/demo/clientes/"))
    assert "Sofia Super" in html and "arquivado" in html

    chave = make_template_fragment_key(
        "v8_menu",
        [s_menu.VERSAO_MENU, s_global.hash_permissoes(superusuario), "demo-clientes"],
    )
    em_cache = cache_real.get(chave)
    assert "Demonstração" in em_cache
    for proprio in [
        "Sofia",
        "Super",
        superusuario.email,
        "super",
        "csrf",
        cliente.cookies["csrftoken"].value,
        "arquivado",
        "v8-avatar",
        "v8-usuario",
        "<form",
        "<script",
    ]:
        assert proprio not in em_cache, proprio


# --- Topbar e breadcrumbs -----------------------------------------------------------


@pytest.mark.spec("V8-SHELL-020")
def test_topbar_tem_marca_botoes_e_area_do_usuario(cache_real, superusuario):
    anonimo = topbar_de(html_de(cliente_http().get("/v8/?a=1&b=dois")))
    assert '<a class="v8-topbar-marca" href="/v8/">PortalCMJ</a>' in anonimo
    # O botão da sidebar só existe no layout que tem sidebar.
    assert 'data-v8-acao="sidebar"' not in anonimo
    assert (
        '<button type="button" class="v8-btn v8-btn-icone" data-v8-acao="sidebar" '
        'aria-controls="v8-sidebar" aria-expanded="true" aria-label="Menu">'
        in topbar_de(pagina_no_layout("app_sidebar"))
    )
    assert (
        '<button type="button" class="v8-btn v8-btn-icone" data-v8-acao="modo" '
        'aria-pressed="false" aria-label="Modo escuro">' in anonimo
    )
    assert 'href="#v8-i-sol"' in anonimo and 'href="#v8-i-lua"' in anonimo
    assert '<div class="v8-usuario">' in anonimo
    assert (
        '<a class="v8-btn v8-btn-fantasma" '
        'href="/login/?next=%2Fv8%2F%3Fa%3D1%26b%3Ddois">Entrar</a>' in anonimo
    )
    assert "Sair" not in anonimo

    cliente = cliente_http(superusuario)
    cliente.cookies["v8_modo"] = "escuro"
    cliente.cookies["v8_sidebar"] = "recolhida"
    autenticado = topbar_de(html_de(cliente.get("/v8/demo/clientes/")))
    assert "Sofia Super" in autenticado
    assert 'href="#v8-i-usuario"' in autenticado
    assert re.search(
        r'<form method="post" action="/logout/">'
        r'<input type="hidden" name="csrfmiddlewaretoken" value="[^"]+">'
        r'<button type="submit" class="v8-btn v8-btn-fantasma">Sair</button></form>',
        autenticado,
    )
    assert "Entrar" not in autenticado
    assert 'aria-expanded="false"' in autenticado
    assert 'aria-pressed="true"' in autenticado

    # Fora de cache: outro usuário, na mesma página, vê os próprios dados.
    outro = criar_usuario("outra", superusuario=True, first_name="Olga")
    outra_topbar = topbar_de(html_de(cliente_http(outro).get("/v8/")))
    assert "Olga" in outra_topbar and "Sofia" not in outra_topbar


@pytest.mark.spec("V8-SHELL-020")
def test_topbar_mostra_o_avatar_quando_ha(superusuario, monkeypatch):
    monkeypatch.setattr(s_global, "_avatar", lambda usuario: "/media/avatar&1.jpg")
    topbar = topbar_de(html_de(cliente_http(superusuario).get("/v8/")))
    assert '<img class="v8-avatar" src="/media/avatar&amp;1.jpg" alt="">' in topbar
    assert 'href="#v8-i-usuario"' not in topbar


@pytest.mark.spec("V8-SHELL-021")
def test_trilha_vem_da_view_e_o_ultimo_item_nao_e_link(superusuario):
    cliente = cliente_http(superusuario)

    def trilha(url):
        return trecho(html_de(cliente.get(url)), '<nav class="v8-trilha"', "</nav>")

    def itens(html):
        return [
            re.sub(r"\s+", " ", li).strip()
            for li in re.findall(r"<li.*?</li>", html, re.S)
        ]

    lista = trilha("/v8/demo/clientes/")
    assert '<nav class="v8-trilha" aria-label="Trilha">' in lista
    assert "<ol data-v8-trilha>" in lista
    assert itens(lista) == [
        '<li><a href="/v8/">Início</a></li>',
        '<li aria-current="page">Clientes</li>',
    ]
    unico = trecho(
        pagina_no_layout("app_topbar", contexto={"v8": {"trilha": [("Só", None)]}}),
        '<nav class="v8-trilha"',
        "</nav>",
    )
    assert itens(unico) == ['<li aria-current="page">Só</li>']

    assert itens(trilha("/v8/demo/clientes/2/")) == [
        '<li><a href="/v8/">Início</a></li>',
        '<li><a href="/v8/demo/clientes/">Clientes</a></li>',
        '<li aria-current="page">Bento Exemplo</li>',
    ]
    assert itens(trilha("/v8/demo/spa/")) == [
        '<li><a href="/v8/">Início</a></li>',
        '<li aria-current="page">Demonstração SPA</li>',
    ]

    # Sem trilha informada, nada é renderizado.
    assert "v8-trilha" not in html_de(cliente.get("/v8/nao-existe/"))


@pytest.mark.spec("V8-SHELL-023")
@pytest.mark.parametrize("layout", ["landing", "app_topbar", "app_sidebar"])
def test_shell_usa_marcos_semanticos_e_link_de_pular(layout):
    html = pagina_no_layout(layout, contexto={"v8": {"trilha": [("Início", None)]}})
    corpo = html[html.index("<body") :]

    assert '<header class="v8-topbar">' in corpo
    assert (
        '<nav id="v8-menu-principal" class="v8-menu" aria-label="Menu principal">'
        in corpo
    )
    assert corpo.count("<main") == 1
    assert '<main id="conteudo" class="v8-main" tabindex="-1">' in corpo
    if layout == "landing":
        assert "<footer" in corpo and "v8-trilha" not in corpo
    else:
        assert '<nav class="v8-trilha" aria-label="Trilha">' in corpo
    if layout == "app_sidebar":
        assert '<aside id="v8-sidebar" class="v8-sidebar">' in corpo

    # O link de pular é o primeiro elemento focável do corpo.
    pular = '<a class="v8-pular" href="#conteudo">Ir para o conteúdo</a>'
    focaveis = re.findall(r"<(?:a|button|input|select|textarea|summary)\b[^>]*>", corpo)
    assert corpo.index(pular) == corpo.index(focaveis[0])


# --- Sidebar e modo ---------------------------------------------------------------


@pytest.mark.spec("V8-SHELL-030")
def test_estado_da_sidebar_vem_do_cookie(superusuario):
    cliente = cliente_http(superusuario)
    assert (
        '<html lang="pt-br" data-tema="oficial" data-sidebar="expandida">'
        in html_de(cliente.get("/v8/demo/clientes/"))
    )

    cliente.cookies["v8_sidebar"] = "recolhida"
    html = html_de(cliente.get("/v8/demo/clientes/"))
    assert '<html lang="pt-br" data-tema="oficial" data-sidebar="recolhida">' in html
    assert (
        'data-v8-acao="sidebar" aria-controls="v8-sidebar" aria-expanded="false"'
        in html
    )
    assert ler_json_script(html, "v8-global")["sidebar"] == "recolhida"

    cliente.cookies["v8_sidebar"] = "expandida"
    assert 'data-sidebar="expandida"' in html_de(cliente.get("/v8/demo/clientes/"))

    # Só o layout com sidebar emite o atributo; o JSON global informa o estado sempre.
    cliente.cookies["v8_sidebar"] = "recolhida"
    for url in ("/v8/", "/v8/demo/layouts/app_topbar/", "/v8/nao-existe/"):
        html = html_de(cliente.get(url))
        assert "data-sidebar" not in html, url
        assert ler_json_script(html, "v8-global")["sidebar"] == "recolhida"


@pytest.mark.spec("V8-SHELL-033")
def test_menu_funciona_sem_javascript(superusuario):
    cliente = cliente_http(superusuario)
    for pagina in (
        "/v8/",
        "/v8/demo/layouts/app_topbar/",
        "/v8/demo/layouts/app_sidebar/",
    ):
        menu = menu_de(html_de(cliente.get(pagina)))
        # Links comuns, com href, e grupos em <details>, que abrem sem script.
        for url in ["/v8/", "/v8/demo/clientes/", "/v8/demo/spa/"]:
            assert f'<a class="v8-menu-link" href="{url}"' in menu
        assert '<details class="v8-menu-grupo"' in menu
        assert '<summary class="v8-menu-link">' in menu
        assert "<button" not in menu

    # Sem script o menu fica visível em qualquer largura, na sidebar e no cabeçalho.
    css = (DIR_CSS_OFICIAL / "shell.css").read_text(encoding="utf-8")
    sem_script = "".join(
        re.findall(r"@media \(scripting: none\)[^{]*{(?:[^{}]*{[^}]*})*\s*}", css)
    )
    assert re.search(r"\.v8-sidebar\s*{\s*display: block;", sem_script)
    assert re.search(r"\.v8-topbar \.v8-menu\s*{\s*display: block;", sem_script)
    assert re.search(r"\.v8-botao-menu\s*{\s*display: none;", sem_script)


@pytest.mark.spec("V8-SHELL-040")
def test_tema_vem_do_cookie_e_sem_cookie_nao_ha_atributo():
    cliente = cliente_http()
    html = html_de(cliente.get("/v8/"))
    assert "data-modo" not in html
    assert ler_json_script(html, "v8-global")["modo"] is None
    assert 'data-v8-acao="modo" aria-pressed="false"' in html

    cliente.cookies["v8_modo"] = "escuro"
    html = html_de(cliente.get("/v8/"))
    assert '<html lang="pt-br" data-tema="oficial" data-modo="escuro">' in html
    assert 'data-v8-acao="modo" aria-pressed="true"' in html
    assert ler_json_script(html, "v8-global")["modo"] == "escuro"

    cliente.cookies["v8_modo"] = "claro"
    html = html_de(cliente.get("/v8/"))
    assert '<html lang="pt-br" data-tema="oficial" data-modo="claro">' in html
    assert 'data-v8-acao="modo" aria-pressed="false"' in html
    assert (
        '<html lang="pt-br" data-tema="oficial" data-modo="claro" data-sidebar="expandida">'
        in pagina_no_layout("app_sidebar", cookies={"v8_modo": "claro"})
    )

    # Vale também no layout sem shell.
    assert 'data-modo="claro"' in html_de(cliente.get("/v8/nao-existe/"))


# --- Requisitos de segurança ---------------------------------------------------------


@pytest.mark.spec("V8-SHELL-051")
def test_cache_real_nao_mistura_menus_de_usuarios_diferentes(
    cache_real, menu_de_teste, superusuario
):
    com_a = com_permissao("tem.a", menu_de_teste["a"])
    com_b = com_permissao("tem.b", menu_de_teste["b"])
    sem = criar_usuario("sem.nada")

    def links(usuario):
        menu = menu_de(html_de(cliente_http(usuario).get("/v8/")))
        return re.findall(r'<a class="v8-menu-link" href="([^"]+)"', menu)

    esperado = {
        superusuario: ["/v8/", "/v8/a/", "/v8/ab/", "/v8/b/", "/v8/r/"],
        com_a: ["/v8/", "/v8/a/", "/v8/ab/"],
        com_b: ["/v8/", "/v8/ab/", "/v8/b/"],
        sem: ["/v8/"],
        None: ["/v8/"],
    }
    # Duas voltas: na segunda, todas as entradas já estão em cache.
    for _ in range(2):
        for usuario, urls in esperado.items():
            assert links(usuario) == urls, usuario


@pytest.mark.spec("V8-SHELL-052")
@pytest.mark.parametrize(
    "valor",
    ["zzqxinvalido", 'zzqx"><b>', "escuro zzqx", "ESCURO", "recolhida-zzqx", "auto"],
)
def test_valor_invalido_de_cookie_nunca_chega_ao_html(valor):
    cliente = cliente_http()
    cliente.cookies["v8_modo"] = valor
    cliente.cookies["v8_sidebar"] = valor
    paginas = [html_de(cliente.get(url)) for url in ("/v8/", "/v8/nao-existe/")]
    paginas.append(
        pagina_no_layout("app_sidebar", cookies={"v8_modo": valor, "v8_sidebar": valor})
    )
    for html in paginas:
        assert "data-modo" not in html
        assert "zzqx" not in html and "ESCURO" not in html
        dados = ler_json_script(html, "v8-global")
        assert dados["modo"] is None and dados["sidebar"] == "expandida"
    # No layout com sidebar, o atributo sai com o valor padrão.
    assert (
        '<html lang="pt-br" data-tema="oficial" data-sidebar="expandida">'
        in paginas[-1]
    )


@pytest.mark.spec("V8-SHELL-053")
def test_entrar_leva_so_caminho_e_query_e_sair_usa_o_logout_existente(superusuario):
    resposta = cliente_http().get(
        "/v8/?volta=https://exemplo.invalid/&x=<b>", headers={"Host": "testserver"}
    )
    topbar = topbar_de(html_de(resposta))
    href = re.search(r'href="(/login/\?next=[^"]*)">Entrar', topbar).group(1)
    retorno = href.split("?next=", 1)[1]
    # Codificado por inteiro: nenhum separador de URL sobra no valor.
    assert re.fullmatch(r"[A-Za-z0-9%._~-]+", retorno)
    assert retorno.startswith(
        "%2Fv8%2F%3Fvolta%3Dhttps%3A%2F%2Fexemplo.invalid%2F%26x%3D"
    )
    assert "testserver" not in href and "http://" not in href

    from urllib.parse import unquote

    assert unquote(retorno).startswith("/v8/?volta=")

    cliente = cliente_http(superusuario)
    topbar = topbar_de(html_de(cliente.get("/v8/")))
    assert '<form method="post" action="/logout/">' in topbar
    # A rota de logout existente encerra a sessão.
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', topbar).group(1)
    resposta = cliente.post("/logout/", {"csrfmiddlewaretoken": token})
    assert resposta.status_code in (200, 302)
    dados = ler_json_script(html_de(cliente.get("/v8/")), "v8-global")
    assert dados["autenticado"] is False
