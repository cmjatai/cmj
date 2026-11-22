"""Testes da spec docs/specs/v8/demo.md, no que cabe ao Django.

Cada teste está ligado a uma regra pelo marker ``spec``.
"""

import copy
import inspect
import json
import re
from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from cmj.v8 import views
from cmj.v8.services import s_demo, s_global
from cmj.v8.tests.conftest import (
    CABECALHOS_CLIENTE,
    CABECALHOS_FRAGMENTO,
    URL_DEMO_FRAGMENTO,
    URLS_DEMO_API,
    URLS_DEMO_LAYOUTS,
    URLS_DEMO_PAGINAS,
    cliente_http,
    html_de,
    ler_json_script,
    trecho,
)

pytestmark = pytest.mark.django_db

CAMPOS_CLIENTE = {
    "id",
    "nome",
    "email",
    "cidade",
    "situacao",
    "motivo",
    "desde",
    "pedidos",
}
CAMPOS_RESUMO = (CAMPOS_CLIENTE - {"pedidos"}) | {"total_pedidos"}
CAMPOS_PEDIDO = {"id", "descricao", "valor", "data"}
CHAVES_LISTA = {"total", "pagina", "paginas", "tamanho", "itens"}

VALIDO = {
    "nome": "Íris Demonstração",
    "email": "iris.demonstracao@exemplo.invalid",
    "cidade": "Jataí",
    "situacao": "ativo",
    "motivo": "",
}


def todos():
    return [s_demo.obter(pk) for pk in range(1, s_demo.TOTAL_CLIENTES + 1)]


def enviar(cliente, metodo, url, dados, **extra):
    return getattr(cliente, metodo)(
        url,
        data=json.dumps(dados),
        content_type="application/json",
        headers={**CABECALHOS_CLIENTE, **extra},
    )


def erros(dados, pk=None):
    cliente, form = s_demo.validar(dados, pk=pk)
    assert cliente is None
    return dict(form.errors)


# --- Dados -------------------------------------------------------------------------


@pytest.mark.spec("V8-DEMO-001")
def test_clientes_sao_uma_lista_fixa_e_ficticia():
    clientes = todos()
    assert len(clientes) == 42 == s_demo.listar(tamanho=50)["total"]
    assert [c["id"] for c in clientes] == list(range(1, 43))
    assert len({c["nome"] for c in clientes}) == 42
    assert len({c["email"] for c in clientes}) == 42
    assert s_demo.obter(43) is None and s_demo.obter(0) is None

    for cliente in clientes:
        assert set(cliente) == CAMPOS_CLIENTE
        assert re.fullmatch(r"[a-z.]+@exemplo\.invalid", cliente["email"])
        assert cliente["situacao"] in ("ativo", "inativo")
        assert bool(cliente["motivo"]) is (cliente["situacao"] == "inativo")
        assert cliente["cidade"] in s_demo.cidades()
        date.fromisoformat(cliente["desde"])
        assert 1 <= len(cliente["pedidos"]) <= 4
        for pedido in cliente["pedidos"]:
            assert set(pedido) == CAMPOS_PEDIDO
            assert re.fullmatch(r"\d+\.\d{2}", pedido["valor"])
            date.fromisoformat(pedido["data"])
    assert len({p["id"] for c in clientes for p in c["pedidos"]}) == sum(
        len(c["pedidos"]) for c in clientes
    )
    assert {c["situacao"] for c in clientes} == {"ativo", "inativo"}
    assert {len(c["pedidos"]) for c in clientes} == {1, 2, 3, 4}
    assert 3 <= len(s_demo.cidades()) <= 8

    # Gerada sem acaso: uma nova geração dá a mesma lista.
    assert list(s_demo._gerar_clientes()) == clientes
    fonte = inspect.getsource(s_demo)
    assert "random" not in fonte and "uuid" not in fonte
    # Sem CPF, telefone nem endereço: só os campos conferidos acima, e nenhum
    # valor com cara de documento ou número de telefone.
    assert not re.search(r"\d{8,}|\d{3}\.\d{3}\.\d{3}", json.dumps(clientes))


@pytest.mark.spec("V8-DEMO-002")
def test_nada_e_gravado_e_as_telas_avisam(superusuario):
    antes = copy.deepcopy(todos())
    cliente = cliente_http(superusuario)

    criado = enviar(cliente, "post", "/v8/demo/api/clientes/", VALIDO)
    assert criado.status_code == 201
    assert criado.json() == {
        **VALIDO,
        "id": 43,
        "desde": date.today().isoformat(),
        "pedidos": [],
    }

    editado = enviar(
        cliente,
        "put",
        "/v8/demo/api/clientes/2/",
        {**VALIDO, "situacao": "inativo", "motivo": "Teste de edição"},
    )
    assert editado.status_code == 200
    assert editado.json() == {
        **antes[1],
        **VALIDO,
        "situacao": "inativo",
        "motivo": "Teste de edição",
    }

    arquivado = cliente.post("/v8/demo/clientes/arquivar/", {"ids": ["1", "2", "3"]})
    assert arquivado.status_code == 302

    # A lista continua a mesma, e quem recebe uma cópia não altera a original.
    s_demo.obter(1)["nome"] = "Alterado"
    s_demo.obter(1)["pedidos"].clear()
    s_demo.listar()["itens"][0]["nome"] = "Alterado"
    assert todos() == antes
    assert cliente.get("/v8/demo/api/clientes/2/").json() == antes[1]
    assert cliente.get("/v8/demo/api/clientes/43/").status_code == 404
    assert cliente.get("/v8/demo/api/clientes/").json()["total"] == 42

    for url in ("/v8/demo/clientes/", "/v8/demo/clientes/2/"):
        aviso = trecho(html_de(cliente.get(url)), '<p class="v8-aviso-demo">', "</p>")
        assert "demonstração" in aviso and "Nada" in aviso


@pytest.mark.spec("V8-DEMO-003")
def test_validacao_de_cliente_e_um_formulario_django():
    from django import forms

    assert issubclass(s_demo.ClienteForm, forms.Form)

    cliente, form = s_demo.validar(VALIDO)
    assert form.is_valid() and cliente["nome"] == VALIDO["nome"]

    # Nome: obrigatório, com ao menos três letras.
    for nome in ["", "   ", "Jó", "A1 2", "12345", "a.b"]:
        assert "nome" in erros({**VALIDO, "nome": nome}), nome
    for nome in ["Ana", "Jó 3 X"]:
        assert s_demo.validar({**VALIDO, "nome": nome})[0], nome

    # E-mail: válido e ainda não usado por outro cliente.
    for email in ["", "sem-arroba", "a@", "@b.invalid"]:
        assert "email" in erros({**VALIDO, "email": email}), email
    de_outro = s_demo.obter(7)["email"]
    assert "email" in erros({**VALIDO, "email": de_outro})
    assert "email" in erros({**VALIDO, "email": de_outro.upper()})
    assert "email" in erros({**VALIDO, "email": de_outro}, pk=8)
    # O próprio cliente pode manter o e-mail.
    assert s_demo.validar({**VALIDO, "email": de_outro}, pk=7)[0]["id"] == 7

    assert "cidade" in erros({**VALIDO, "cidade": ""})
    assert "situacao" in erros({**VALIDO, "situacao": "suspenso"})
    assert "situacao" in erros({k: v for k, v in VALIDO.items() if k != "situacao"})

    # Situação "inativo" só com motivo: erro geral, não de campo.
    for motivo in ["", "   "]:
        achados = erros({**VALIDO, "situacao": "inativo", "motivo": motivo})
        assert list(achados) == ["__all__"]
    _, form = s_demo.validar({**VALIDO, "situacao": "inativo"})
    assert form.non_field_errors() == [
        "Cliente inativo precisa de um motivo preenchido."
    ]
    assert s_demo.validar({**VALIDO, "situacao": "inativo", "motivo": "Mudou-se"})[0]

    # Só os campos do formulário entram no registro.
    cliente, _ = s_demo.validar({**VALIDO, "id": 999, "pedidos": [1], "extra": "x"})
    assert set(cliente) == CAMPOS_CLIENTE
    assert cliente["id"] == 43 and cliente["pedidos"] == []
    assert s_demo.validar("texto")[0] is None
    with pytest.raises(LookupError):
        s_demo.validar(VALIDO, pk=999)


# --- Página Django com ilhas ------------------------------------------------------------


@pytest.mark.spec("V8-DEMO-010")
def test_lista_e_renderizada_filtrada_e_paginada_no_servidor(superusuario):
    cliente = cliente_http(superusuario)

    def pagina(consulta=""):
        resposta = cliente.get("/v8/demo/clientes/" + consulta)
        assert resposta.status_code == 200
        html = html_de(resposta)
        return html, re.findall(r'<a href="/v8/demo/clientes/(\d+)/" data-drawer', html)

    html, ids = pagina()
    assert 'class="v8-shell"' in html
    assert ids == [str(n) for n in range(1, 11)]
    assert "42 clientes encontrados." in html
    paginacao = trecho(
        html, '<nav class="v8-paginacao" aria-label="Paginação">', "</nav>"
    )
    assert re.findall(r'href="([^"]+)"', paginacao) == [
        "/v8/demo/clientes/",
        "/v8/demo/clientes/?pagina=2",
        "/v8/demo/clientes/?pagina=3",
        "/v8/demo/clientes/?pagina=4",
        "/v8/demo/clientes/?pagina=5",
        "/v8/demo/clientes/?pagina=2",
    ]
    assert paginacao.count('aria-current="page"') == 1

    _, ids = pagina("?pagina=5")
    assert ids == ["41", "42"]
    # Página fora do intervalo ou inválida é trazida para o intervalo.
    assert pagina("?pagina=99")[1] == ["41", "42"]
    assert pagina("?pagina=abc")[1] == pagina("?pagina=-3")[1] == pagina()[1]

    # Filtros, sozinhos e combinados, conferidos contra os dados.
    clientes = todos()
    inativos = [str(c["id"]) for c in clientes if c["situacao"] == "inativo"]
    html, ids = pagina("?situacao=inativo")
    assert ids == inativos[:10] and f"{len(inativos)} clientes encontrados." in html
    assert '<option value="inativo" selected>' in html

    de_jatai = [str(c["id"]) for c in clientes if c["cidade"] == "Jataí"]
    html, ids = pagina("?cidade=Jata%C3%AD")
    assert ids == de_jatai[:10]
    assert '<option value="Jataí" selected>' in html

    html, ids = pagina("?q=GLORIA")
    assert ids == [str(c["id"]) for c in clientes if c["nome"].startswith("Glória")]
    assert 'name="q" value="GLORIA"' in html
    assert pagina("?q=modelo@exemplo")[1] == [
        str(c["id"]) for c in clientes if "Modelo" in c["nome"]
    ]

    combinados = [
        str(c["id"])
        for c in clientes
        if c["situacao"] == "ativo"
        and c["cidade"] == "Mineiros"
        and "Teste" in c["nome"]
    ]
    html, ids = pagina("?q=teste&situacao=ativo&cidade=Mineiros")
    assert ids == combinados and combinados

    # Os links de paginação mantêm os filtros.
    html, ids = pagina("?situacao=ativo&q=e&pagina=2")
    paginacao = trecho(html, '<nav class="v8-paginacao"', "</nav>")
    links = [
        link.replace("&amp;", "&") for link in re.findall(r'href="([^"]+)"', paginacao)
    ]
    assert links[0] == "/v8/demo/clientes/?q=e&situacao=ativo"
    assert "/v8/demo/clientes/?q=e&situacao=ativo&pagina=3" in links
    assert ids and all(
        "e" in s_demo.obter(int(i))["nome"].lower() + s_demo.obter(int(i))["email"]
        for i in ids
    )

    # Sem resultado, a página diz isso e não tem paginação.
    html, ids = pagina("?q=ninguem-com-este-nome")
    assert ids == [] and "Nenhum cliente encontrado" in html
    assert "v8-paginacao" not in html

    # Sem JavaScript: filtro por GET, detalhe por link e arquivar por POST.
    html, _ = pagina()
    filtros = trecho(html, '<form id="demo-filtros"', "</form>")
    assert 'method="get" action="/v8/demo/clientes/"' in filtros
    for campo in ('name="q"', 'name="situacao"', 'name="cidade"', 'type="submit"'):
        assert campo in filtros
    assert (
        '<a class="v8-btn v8-btn-fantasma" href="/v8/demo/clientes/">Limpar</a>'
        in filtros
    )
    assert (
        '<input type="checkbox" name="ids" value="3" form="demo-arquivar" '
        'aria-label="Selecionar Clara Exemplo">' in html
    )

    detalhe = html_de(cliente.get("/v8/demo/clientes/3/"))
    registro = s_demo.obter(3)
    assert '<dl class="v8-lista-dados">' in detalhe
    for texto in [registro["nome"], registro["email"], registro["cidade"]]:
        assert texto in detalhe
    for pedido in registro["pedidos"]:
        assert pedido["descricao"] in detalhe
    assert 'href="/v8/demo/clientes/">Voltar para a lista</a>' in detalhe


@pytest.mark.spec("V8-DEMO-011")
@pytest.mark.spec("V8-DEMO-012")
@pytest.mark.spec("V8-DEMO-013")
@pytest.mark.spec("V8-DEMO-014")
def test_marcacao_que_o_frontend_usa_na_pagina_de_clientes(superusuario):
    """Só a parte do servidor: os atributos de que a ilha e os drawers dependem."""
    cliente = cliente_http(superusuario)
    html = html_de(cliente.get("/v8/demo/clientes/?pagina=2"))

    # A tabela é a ilha, com o HTML do servidor como espera e a página nas props.
    ilha = re.search(
        r'<div data-vue-island="demo-clientes-tabela" data-props-id="(v8-island-\d+)">'
        r'\s*<table class="v8-tabela">',
        html,
    )
    assert ilha
    assert ler_json_script(html, ilha.group(1)) == {
        "clientes": s_demo.listar(pagina=2)["itens"],
        "formulario": "demo-arquivar",
    }

    assert (
        '<form id="demo-filtros" method="get" action="/v8/demo/clientes/" '
        'data-drawer-auto data-drawer-side="left" data-drawer-size="sm" '
        'data-drawer-mode="docked" '
        'data-drawer-mode-estreito="overlay" data-drawer-title="Filtros">' in html
    )
    assert (
        '<button type="button" class="v8-btn" data-drawer="el:#demo-filtros" '
        'data-drawer-side="left" data-drawer-title="Filtros">Filtros</button>' in html
    )
    assert (
        '<a href="/v8/demo/clientes/11/" data-drawer="cliente:11" '
        'data-drawer-side="right">' in html
    )

    detalhe = html_de(cliente.get("/v8/demo/clientes/11/"))
    assert (
        '<a class="v8-btn" href="/v8/_frag/demo/cliente/11/historico/" '
        'data-drawer="frag:demo/cliente/11/historico" data-drawer-side="right">'
        "Histórico</a>" in detalhe
    )
    # O link sem JavaScript leva ao mesmo conteúdo do drawer.
    assert cliente.get("/v8/_frag/demo/cliente/11/historico/").status_code == 200


@pytest.mark.spec("V8-DEMO-015")
def test_arquivar_e_post_com_confirmacao_mensagem_e_redirecionamento(superusuario):
    cliente = cliente_http(superusuario)
    html = html_de(cliente.get("/v8/demo/clientes/"))
    assert re.search(
        r'<form id="demo-arquivar" method="post" action="/v8/demo/clientes/arquivar/" '
        r'data-confirm="Arquivar os clientes selecionados\?" '
        r'data-confirm-title="Arquivar clientes" data-confirm-ok="Arquivar">'
        r'<input type="hidden" name="csrfmiddlewaretoken" value="[^"]+">'
        r'<button type="submit" class="v8-btn v8-btn-perigo">Arquivar selecionados'
        r"</button></form>",
        html,
    )

    def arquivar(ids):
        resposta = cliente.post("/v8/demo/clientes/arquivar/", {"ids": ids})
        assert resposta.status_code == 302
        assert resposta["Location"] == "/v8/demo/clientes/"
        seguinte = html_de(cliente.get(resposta["Location"]))
        return ler_json_script(seguinte, "v8-messages"), seguinte

    # Só os ids de clientes existentes contam, uma vez cada.
    mensagens, pagina = arquivar(["3", "7", "7", "999", "abc", ""])
    assert mensagens == [
        {
            "nivel": "success",
            "texto": "2 cliente(s) arquivado(s). Demonstração: nada foi gravado.",
        }
    ]
    # Sem JavaScript não há toast: a mensagem também está no HTML.
    assert re.search(
        r'<noscript>\s*<p class="v8-alerta v8-alerta-sucesso">2 cliente\(s\) arquivado',
        pagina,
    )

    mensagens, pagina = arquivar([])
    assert mensagens == [
        {"nivel": "warning", "texto": "Nenhum cliente selecionado para arquivar."}
    ]
    assert '<p class="v8-alerta v8-alerta-aviso">Nenhum cliente selecionado' in pagina

    assert s_demo.arquivar(None) == 0
    assert s_demo.arquivar([1, "2", 2, None, "x", 43]) == 2


# --- Páginas dos layouts -------------------------------------------------------------


@pytest.mark.spec("V8-DEMO-040")
def test_cada_layout_tem_pagina_de_demonstracao_com_blocks_e_links(superusuario):
    cliente = cliente_http(superusuario)
    paginas = s_demo.layouts_demo()
    assert [p["nome"] for p in paginas] == list(s_global.LAYOUTS)
    assert [p["url"] for p in paginas] == URLS_DEMO_LAYOUTS
    assert s_demo.layout_demo("outro") is None

    for pagina in paginas:
        html = html_de(cliente.get(pagina["url"]))
        assert f'data-v8-layout="{pagina["nome"]}"' in html
        assert f'<h1 class="v8-pagina-titulo">Layout {pagina["nome"]}</h1>' in html
        assert '<p class="v8-aviso-demo">' in html
        assert f'<p>{pagina["resumo"]}</p>' in html
        for bloco, uso in pagina["regioes"]:
            assert f"<dt>{bloco}</dt>" in html and f"<dd>{uso}</dd>" in html
        # Links para as quatro páginas, com a atual marcada.
        navegacao = trecho(html, '<nav class="v8-barra-acoes"', "</nav>")
        links = re.findall(r'href="([^"]+)"( aria-current="page")?', navegacao)
        assert [url for url, _ in links] == URLS_DEMO_LAYOUTS
        assert [url for url, atual in links if atual] == [pagina["url"]]


@pytest.mark.spec("V8-DEMO-041")
def test_landing_preenche_hero_e_rodape_e_o_menu_marca_cada_pagina(superusuario):
    cliente = cliente_http(superusuario)
    html = html_de(cliente.get("/v8/demo/layouts/landing/"))
    hero = trecho(html, '<section class="v8-hero">', "</section>")
    assert "<code>hero</code>" in hero and "Layout landing" in hero
    rodape = trecho(html, '<footer class="v8-rodape">', "</footer>")
    assert "<code>footer_nav</code>" in rodape and "<code>footer_info</code>" in rodape
    assert html.index("</section>") < html.index('<div class="v8-conteudo">')

    for url in URLS_DEMO_LAYOUTS:
        html = html_de(cliente.get(url))
        if url.endswith("/minimal/"):
            assert "v8-menu-principal" not in html
            continue
        menu = trecho(html, '<nav id="v8-menu-principal"', "</nav>")
        assert f'<a class="v8-menu-link" href="{url}" aria-current="page">' in menu
        assert menu.count('aria-current="page"') == 1
        assert '<details class="v8-menu-grupo" open>' in menu


# --- Requisitos de segurança --------------------------------------------------------


@pytest.mark.spec("V8-DEMO-030")
def test_todas_as_rotas_da_demonstracao_exigem_superusuario(
    comum, superusuario, settings
):
    import cmj.v8.urls

    rotas_demo = [
        r for r in cmj.v8.urls.urlpatterns if "demo" in r.pattern.regex.pattern
    ]
    assert len(rotas_demo) == 12
    for rota in rotas_demo:
        classe = rota.callback.view_class
        exige = (
            s_global.ZONAS[rota.callback.view_initkwargs["zona"]].exige
            if issubclass(classe, views.ZonaV8View)
            else classe.exige
        )
        assert exige == s_global.SUPERUSUARIO, rota

    # Em qualquer ambiente: com DEBUG ligado ou desligado.
    for debug in (False, True):
        settings.DEBUG = debug
        for url in URLS_DEMO_PAGINAS:
            anonimo = cliente_http().get(url)
            assert anonimo.status_code == 302, url
            assert anonimo["Location"] == f"/login/?next={url}"
            negado = cliente_http(comum).get(url)
            assert negado.status_code == 403, url
            assert 'class="v8-nua"' in html_de(negado)
            assert "Acesso negado" in html_de(negado)
            assert cliente_http(superusuario).get(url).status_code == 200, url

        for url in URLS_DEMO_API + [URL_DEMO_FRAGMENTO]:
            cabecalhos = (
                CABECALHOS_FRAGMENTO
                if url == URL_DEMO_FRAGMENTO
                else CABECALHOS_CLIENTE
            )
            anonimo = cliente_http().get(url, headers=cabecalhos)
            assert anonimo.status_code == 401, url
            assert anonimo.json()["code"] == "nao_autenticado"
            negado = cliente_http(comum).get(url, headers=cabecalhos)
            assert negado.status_code == 403, url
            assert negado.json()["code"] == "sem_permissao"

    # Escrita e ação em massa também.
    for cliente, status in ((cliente_http(), 401), (cliente_http(comum), 403)):
        assert (
            enviar(cliente, "post", "/v8/demo/api/clientes/", VALIDO).status_code
            == status
        )
        assert (
            enviar(cliente, "put", "/v8/demo/api/clientes/1/", VALIDO).status_code
            == status
        )
    assert (
        cliente_http().post("/v8/demo/clientes/arquivar/", {"ids": ["1"]}).status_code
        == 302
    )
    assert (
        cliente_http(comum)
        .post("/v8/demo/clientes/arquivar/", {"ids": ["1"]})
        .status_code
        == 403
    )

    # Usuário inativo marcado como superusuário não passa.
    comum.is_superuser, comum.is_active = True, False
    assert (
        s_global.situacao_acesso(comum, s_global.SUPERUSUARIO) == s_global.SEM_PERMISSAO
    )


@pytest.mark.spec("V8-DEMO-025")
@pytest.mark.spec("V8-DEMO-030")
def test_endpoint_negado_responde_403_ate_para_superusuario(superusuario):
    resposta = cliente_http(superusuario).get(
        "/v8/demo/api/negado/", headers=CABECALHOS_CLIENTE
    )
    assert resposta.status_code == 403
    assert resposta.json()["code"] == "sem_permissao"
    assert resposta.json()["detail"]


@pytest.mark.spec("V8-DEMO-031")
def test_escrita_simulada_so_por_post_ou_put_com_csrf(superusuario):
    cliente = cliente_http(superusuario, enforce_csrf_checks=True)
    cliente.get("/v8/demo/clientes/")
    token = cliente.cookies["csrftoken"].value

    # Sem o token, recusado. Com o cabeçalho que o cliente HTTP envia, aceito.
    assert enviar(cliente, "post", "/v8/demo/api/clientes/", VALIDO).status_code == 403
    assert enviar(cliente, "put", "/v8/demo/api/clientes/1/", VALIDO).status_code == 403
    assert (
        cliente.post("/v8/demo/clientes/arquivar/", {"ids": ["1"]}).status_code == 403
    )
    com_token = {"X-CSRFToken": token}
    assert (
        enviar(
            cliente, "post", "/v8/demo/api/clientes/", VALIDO, **com_token
        ).status_code
        == 201
    )
    assert (
        enviar(
            cliente, "put", "/v8/demo/api/clientes/1/", VALIDO, **com_token
        ).status_code
        == 200
    )
    assert (
        cliente.post(
            "/v8/demo/clientes/arquivar/", {"ids": ["1"]}, headers=com_token
        ).status_code
        == 302
    )

    # Cada endpoint aceita só os métodos previstos.
    livre = cliente_http(superusuario)
    aceitos = {
        "/v8/demo/api/clientes/": {"get", "post"},
        "/v8/demo/api/clientes/1/": {"get", "put"},
        "/v8/demo/api/negado/": {"get"},
        "/v8/demo/clientes/arquivar/": {"post"},
    }
    for url, metodos in aceitos.items():
        for metodo in ("get", "post", "put", "patch", "delete"):
            corpo = {} if metodo == "get" else {"data": "{}"}
            status = getattr(livre, metodo)(
                url, content_type="application/json", **corpo
            ).status_code
            assert (status == 405) is (metodo not in metodos), (metodo, url, status)

    # Dados na query string de um GET não simulam escrita.
    resposta = livre.get("/v8/demo/api/clientes/1/?nome=Outro")
    assert resposta.json() == s_demo.obter(1)


@pytest.mark.spec("V8-DEMO-032")
def test_id_inexistente_da_404_e_filtros_e_tamanho_tem_limite(superusuario):
    cliente = cliente_http(superusuario)

    pagina = cliente.get("/v8/demo/clientes/999/")
    assert pagina.status_code == 404
    assert 'class="v8-nua"' in html_de(pagina)
    assert pagina["Content-Type"].startswith("text/html")

    for url in ["/v8/demo/api/clientes/999/", "/v8/demo/api/clientes/0/"]:
        api = cliente.get(url)
        assert api.status_code == 404
        assert api.json() == {"detail": "Não encontrado."}
    assert (
        enviar(cliente, "put", "/v8/demo/api/clientes/999/", VALIDO).status_code == 404
    )

    fragmento = cliente.get(
        "/v8/_frag/demo/cliente/999/historico/", headers=CABECALHOS_FRAGMENTO
    )
    assert fragmento.status_code == 404
    assert fragmento.json() == {"detail": "Não encontrado."}
    assert cliente.get("/v8/_frag/demo/cliente/999/historico/").status_code == 404
    assert s_demo.historico(999) is None

    # Id grande demais para virar número também é 404.
    assert cliente.get(f"/v8/demo/api/clientes/{'9' * 5000}/").status_code == 404

    def api(consulta):
        resposta = cliente.get("/v8/demo/api/clientes/" + consulta)
        assert resposta.status_code == 200
        return resposta.json()

    # O tamanho da página tem máximo e mínimo.
    assert api("")["tamanho"] == 10
    grande = api("?tamanho=100000")
    assert grande["tamanho"] == 50 == s_demo.TAMANHO_MAXIMO
    assert len(grande["itens"]) == 42 and grande["paginas"] == 1
    assert api("?tamanho=0")["tamanho"] == 1
    assert api("?tamanho=-5")["tamanho"] == 1
    assert api("?tamanho=abc")["tamanho"] == 10
    assert api("?tamanho=5&pagina=3")["itens"][0]["id"] == 11
    assert api("?pagina=999")["pagina"] == 5
    assert s_demo.listar(tamanho=10**9)["tamanho"] == 50

    # Só q, situacao e cidade filtram. O resto é ignorado.
    todos_os_ids = [c["id"] for c in api("?tamanho=50")["itens"]]
    for ignorado in [
        "?email=ana.exemplo@exemplo.invalid",
        "?id=1&nome=Ana",
        "?motivo=Cadastro&ordem=-id&desde__gte=2022-01-01",
        "?situacao=suspenso",
        "?cidade=Lugar%20Nenhum",
        "?situacao__in=ativo",
    ]:
        assert [c["id"] for c in api(ignorado + "&tamanho=50")["itens"]] == todos_os_ids
    assert api("?situacao=inativo&cidade=jatai&q=a")["total"] == len(
        [
            c
            for c in todos()
            if c["situacao"] == "inativo"
            and c["cidade"] == "Jataí"
            and "a" in c["nome"].lower() + c["email"]
        ]
    )
    assert set(inspect.signature(s_demo.listar).parameters) == {
        "q",
        "situacao",
        "cidade",
        "pagina",
        "tamanho",
    }
    # A busca tem tamanho máximo.
    assert len(s_demo.normalizar_filtros(q="x" * 5000)["q"]) == 100


@pytest.mark.spec("V8-DEMO-033")
def test_demonstracao_nao_le_nem_grava_model_arquivo_cache_fila_ou_indice():
    fonte = inspect.getsource(s_demo)
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
        s_demo.listar(q="a", situacao="ativo", cidade="Jataí", pagina=2, tamanho=5)
        s_demo.obter(1)
        s_demo.cidades()
        s_demo.validar(VALIDO)
        s_demo.validar({**VALIDO, "email": "x"}, pk=2)
        s_demo.arquivar(["1", "2"])
        s_demo.historico(4)
    assert len(consultas) == 0

    # As views da demonstração não usam o cache nem outro serviço de dados.
    fonte_views = inspect.getsource(views)
    for proibido in ("models", "django.db", "django.core.cache", "celery", "open("):
        assert proibido not in fonte_views, proibido


@pytest.mark.spec("V8-DEMO-034")
def test_respostas_da_api_tem_so_os_campos_ficticios(superusuario):
    cliente = cliente_http(superusuario)

    lista = cliente.get("/v8/demo/api/clientes/?tamanho=50").json()
    assert set(lista) == CHAVES_LISTA
    assert (lista["total"], lista["pagina"], lista["paginas"]) == (42, 1, 1)
    for item in lista["itens"]:
        assert set(item) == CAMPOS_RESUMO
        assert item["total_pedidos"] == len(s_demo.obter(item["id"])["pedidos"])
    assert lista == s_demo.listar(tamanho=50)

    detalhe = cliente.get("/v8/demo/api/clientes/4/").json()
    assert set(detalhe) == CAMPOS_CLIENTE
    assert all(set(p) == CAMPOS_PEDIDO for p in detalhe["pedidos"])
    assert detalhe == s_demo.obter(4)

    criado = enviar(cliente, "post", "/v8/demo/api/clientes/", {**VALIDO, "extra": 1})
    editado = enviar(cliente, "put", "/v8/demo/api/clientes/4/", {**VALIDO, "id": 77})
    assert set(criado.json()) == set(editado.json()) == CAMPOS_CLIENTE
    assert editado.json()["id"] == 4

    # Nada do usuário da requisição vai nas respostas.
    for resposta in (criado, editado, cliente.get("/v8/demo/api/clientes/")):
        texto = resposta.content.decode()
        assert superusuario.email not in texto and "Sofia" not in texto

    eventos = s_demo.historico(4)
    assert all(set(e) == {"data", "texto"} for e in eventos)
    assert [e["data"] for e in eventos] == sorted(e["data"] for e in eventos)
