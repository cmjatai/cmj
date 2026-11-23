"""Temas e modos do v8 (docs/specs/v8/temas.md)."""

import re

import pytest

from cmj.v8.services import s_global

from .conftest import (
    DIR_CSS_V8,
    DIR_TEMPLATES_V8,
    cliente_http,
    html_de,
    ler_json_script,
    pagina_no_layout,
    trecho,
)

pytestmark = pytest.mark.django_db

LAYOUTS = list(s_global.LAYOUTS)


def atributos_html(html):
    """A tag ``<html ...>`` da página."""
    return re.search(r"<html[^>]*>", html).group(0)


# --- Registro ---------------------------------------------------------------------


@pytest.mark.spec("V8-TEMA-002")
def test_registro_de_temas_tem_o_oficial_primeiro_e_nomes_validos():
    assert s_global.TEMA_PADRAO == "oficial"
    assert list(s_global.TEMAS)[0] == "oficial"
    assert list(s_global.TEMAS) == ["oficial", "verde", "terracota", "contraste"]
    assert all(isinstance(rotulo, str) and rotulo for rotulo in s_global.TEMAS.values())
    assert s_global.validar_temas({"oficial": "O", "azul-2": "A"}) == {
        "oficial": "O",
        "azul-2": "A",
    }
    invalidos = [
        {},
        {"verde": "Sem o oficial primeiro", "oficial": "Oficial"},
        {"oficial": "O", "Azul": "Maiúscula"},
        {"oficial": "O", "2azul": "Começa por dígito"},
        {"oficial": "O", "azul escuro": "Espaço"},
        {"oficial": "O", "../x": "Caminho"},
        {"oficial": "O", "escuro": "Nome de modo"},
        {"oficial": "O", "claro": "Nome de modo"},
    ]
    for registro in invalidos:
        with pytest.raises(ValueError):
            s_global.validar_temas(registro)


@pytest.mark.spec("V8-TEMA-003")
def test_cada_tema_do_registro_tem_pasta_e_import_na_mesma_ordem():
    pasta_temas = DIR_CSS_V8 / "temas"
    pastas = sorted(p.name for p in pasta_temas.iterdir() if p.is_dir())
    assert pastas == sorted(s_global.TEMAS)
    for nome in s_global.TEMAS:
        assert (pasta_temas / nome / "index.css").is_file(), nome

    app = re.sub(
        r"/\*.*?\*/", "", (DIR_CSS_V8 / "app.css").read_text("utf-8"), flags=re.S
    )
    importados = re.findall(r'@import\s+"\./temas/([^/"]+)/index\.css"', app)
    assert importados == list(s_global.TEMAS)
    # Nenhum outro CSS de tema entra por fora do index.css de cada pasta.
    assert re.findall(r'@import\s+"([^"]+)"', app) == ["tailwindcss"] + [
        f"./temas/{nome}/index.css" for nome in s_global.TEMAS
    ]


# --- Aplicação ----------------------------------------------------------------------


@pytest.mark.spec("V8-TEMA-020")
def test_html_sempre_traz_um_tema_do_registro():
    for layout in LAYOUTS:
        # Sem cookie: o oficial.
        assert 'data-tema="oficial"' in atributos_html(pagina_no_layout(layout)), layout
        # Com cookie válido: o do cookie.
        html = pagina_no_layout(layout, cookies={"v8_tema": "terracota"})
        assert 'data-tema="terracota"' in atributos_html(html), layout
        # A página de prévia fixa o tema e vence o cookie.
        html = pagina_no_layout(
            layout, cookies={"v8_tema": "terracota"}, contexto={"v8": {"tema": "contraste"}}
        )
        assert 'data-tema="contraste"' in atributos_html(html), layout
        # Prévia com nome fora do registro não vale: fica o do cookie.
        html = pagina_no_layout(
            layout, cookies={"v8_tema": "verde"}, contexto={"v8": {"tema": "zzqx"}}
        )
        assert 'data-tema="verde"' in atributos_html(html), layout
        assert "zzqx" not in html

    resposta = cliente_http().get("/v8/")
    assert '<html lang="pt-br" data-tema="oficial">' in html_de(resposta)
    cliente = cliente_http()
    cliente.cookies["v8_tema"] = "verde"
    assert '<html lang="pt-br" data-tema="verde">' in html_de(cliente.get("/v8/"))
    # Vale também no layout sem shell.
    assert 'data-tema="verde"' in atributos_html(
        html_de(cliente.get("/v8/nao-existe/"))
    )


@pytest.mark.spec("V8-TEMA-001")
def test_tema_e_modo_sao_independentes():
    cliente = cliente_http()
    cliente.cookies["v8_tema"] = "verde"
    cliente.cookies["v8_modo"] = "escuro"
    html = html_de(cliente.get("/v8/"))
    assert '<html lang="pt-br" data-tema="verde" data-modo="escuro">' in html

    cliente.cookies["v8_modo"] = "claro"
    assert 'data-tema="verde" data-modo="claro"' in html_de(cliente.get("/v8/"))

    cliente.cookies["v8_tema"] = "contraste"
    assert 'data-tema="contraste" data-modo="claro"' in html_de(cliente.get("/v8/"))
    # Os dois valores de modo valem em qualquer tema.
    for tema in s_global.TEMAS:
        for modo in s_global.MODOS:
            lido = s_global.preferencias({"v8_tema": tema, "v8_modo": modo})
            assert (lido["tema"], lido["modo"]) == (tema, modo)


@pytest.mark.spec("V8-TEMA-021")
def test_json_global_informa_tema_e_modo():
    cliente = cliente_http()
    dados = ler_json_script(html_de(cliente.get("/v8/")), "v8-global")
    assert dados["tema"] == "oficial" and dados["modo"] is None

    cliente.cookies["v8_tema"] = "terracota"
    cliente.cookies["v8_modo"] = "escuro"
    dados = ler_json_script(html_de(cliente.get("/v8/")), "v8-global")
    assert dados["tema"] == "terracota" and dados["modo"] == "escuro"

    for invalido in ["zzqx", "", "Oficial", "escuro", "../verde"]:
        cliente.cookies["v8_tema"] = invalido
        dados = ler_json_script(html_de(cliente.get("/v8/")), "v8-global")
        assert dados["tema"] == "oficial", invalido


# --- Requisitos de segurança ---------------------------------------------------------


@pytest.mark.spec("V8-TEMA-044")
def test_menu_em_cache_nao_depende_do_tema(cache_real, superusuario):
    menu = (DIR_TEMPLATES_V8 / "v8" / "shell" / "menu.html").read_text("utf-8")
    linha_cache = next(linha for linha in menu.splitlines() if "{% cache" in linha)
    assert "tema" not in linha_cache and "modo" not in linha_cache

    def menu_com(tema):
        cliente = cliente_http(superusuario)
        cliente.cookies["v8_tema"] = tema
        html = html_de(cliente.get("/v8/"))
        return trecho(html, '<nav id="v8-menu-principal"', "</nav>")

    menus = {menu_com(tema) for tema in s_global.TEMAS}
    assert len(menus) == 1
    # O CSS de todos os temas é o mesmo arquivo: a base não escolhe folha por tema.
    base = (DIR_TEMPLATES_V8 / "base_v8.html").read_text("utf-8")
    assert base.count("vite_asset") == 1
