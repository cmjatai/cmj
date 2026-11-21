"""Testes da spec docs/specs/v8/overlays.md, no que cabe ao Django.

Cada teste está ligado a uma regra pelo marker ``spec``.
"""

import re

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

from cmj.v8 import views
from cmj.v8.services import s_demo, s_global
from cmj.v8.tests.conftest import (
    CABECALHOS_CLIENTE,
    CABECALHOS_FRAGMENTO,
    URL_DEMO_FRAGMENTO,
    cliente_http,
    html_de,
)

pytestmark = pytest.mark.django_db

TEMPLATE_HISTORICO = "v8/partials/demo/cliente_historico.html"


class FragmentoPublico(views.FragmentoV8View):
    """Fragmento que não exige autenticação e se declara público."""

    template_name = TEMPLATE_HISTORICO
    publico = True

    def get(self, request):
        return self.responder_fragmento({"cliente": {"nome": "Público"}, "eventos": []})


class FragmentoRestritoDeclaradoPublico(FragmentoPublico):
    exige = s_global.SUPERUSUARIO


def chamar(classe, usuario=None):
    request = RequestFactory().get("/v8/_frag/teste/", headers=CABECALHOS_FRAGMENTO)
    request.user = usuario or AnonymousUser()
    return classe.as_view()(request)


@pytest.mark.spec("V8-OVL-090")
def test_fragmento_devolve_so_o_html_do_template_de_partials(superusuario):
    resposta = cliente_http(superusuario).get(
        URL_DEMO_FRAGMENTO, headers=CABECALHOS_FRAGMENTO
    )
    html = html_de(resposta)
    assert resposta.status_code == 200
    assert resposta["Content-Type"].startswith("text/html")
    assert html.strip().startswith("<section>")
    assert html.strip().endswith("</section>")
    for do_layout in ["<html", "<head", "<body", "v8-global", "v8-shell", "cmj-v8-app"]:
        assert do_layout not in html, do_layout

    cliente = s_demo.obter(1)
    assert f"<h2 data-overlay-title>Histórico de {cliente['nome']}</h2>" in html
    assert html.count("<li>") == len(s_demo.historico(1))

    # O template de um fragmento só pode estar em v8/partials/.
    assert views.DemoClienteHistoricoFragmento.template_name.startswith("v8/partials/")

    class ForaDaPasta(FragmentoPublico):
        template_name = "v8/erros/404.html"

    with pytest.raises(ValueError):
        chamar(ForaDaPasta)


@pytest.mark.spec("V8-OVL-091")
def test_fragmento_e_privado_salvo_o_publico_sem_autenticacao(superusuario):
    resposta = cliente_http(superusuario).get(URL_DEMO_FRAGMENTO)
    assert resposta["Cache-Control"] == "private"

    publica = chamar(FragmentoPublico)
    assert publica.status_code == 200
    assert publica["Cache-Control"] == "public"

    # Declarar-se público não vale para fragmento que exige autenticação.
    restrita = chamar(FragmentoRestritoDeclaradoPublico, superusuario)
    assert restrita.status_code == 200
    assert restrita["Cache-Control"] == "private"
    recusada = chamar(FragmentoRestritoDeclaradoPublico)
    assert recusada.status_code == 401
    assert recusada["Cache-Control"] == "private"

    assert views.FragmentoV8View.publico is False


@pytest.mark.spec("V8-OVL-092")
def test_fragmento_sem_autenticacao_recebe_401_em_json():
    for cabecalhos in (CABECALHOS_FRAGMENTO, CABECALHOS_CLIENTE):
        resposta = cliente_http().get(URL_DEMO_FRAGMENTO, headers=cabecalhos)
        assert resposta.status_code == 401
        assert resposta["Content-Type"] == "application/json"
        assert resposta.json()["code"] == "nao_autenticado"
        assert "Location" not in resposta


@pytest.mark.spec("V8-OVL-101")
def test_fragmento_confere_o_acesso_por_conta_propria(comum, superusuario):
    # Pela URL direta ou pelo cliente HTTP, o resultado é o mesmo.
    direto = cliente_http(superusuario).get(URL_DEMO_FRAGMENTO)
    pelo_drawer = cliente_http(superusuario).get(
        URL_DEMO_FRAGMENTO, headers=CABECALHOS_FRAGMENTO
    )
    assert direto.status_code == pelo_drawer.status_code == 200
    assert direto.content == pelo_drawer.content

    for cabecalhos in ({}, CABECALHOS_FRAGMENTO):
        resposta = cliente_http(comum).get(URL_DEMO_FRAGMENTO, headers=cabecalhos)
        assert resposta.status_code == 403
        assert "Histórico de" not in html_de(resposta)
    assert resposta.json()["code"] == "sem_permissao"

    anonimo = cliente_http().get(URL_DEMO_FRAGMENTO)
    assert anonimo.status_code == 302
    assert anonimo["Location"] == f"/login/?next={URL_DEMO_FRAGMENTO}"

    assert views.DemoClienteHistoricoFragmento.exige == s_global.SUPERUSUARIO


@pytest.mark.spec("V8-OVL-103")
def test_template_do_fragmento_mantem_o_autoescape():
    html = render_to_string(
        TEMPLATE_HISTORICO,
        {
            "cliente": {"nome": '<script>alert(1)</script> & "aspas"'},
            "eventos": [
                {"data": "2024-01-31", "texto": "<img src=x onerror=alert(2)>"},
                {"data": '"><script>alert(3)</script>', "texto": "ok"},
            ],
        },
    )
    assert "<script" not in html and "<img" not in html
    assert (
        "Histórico de &lt;script&gt;alert(1)&lt;/script&gt; &amp; &quot;aspas&quot;"
        in html
    )
    assert "&lt;img src=x onerror=alert(2)&gt;" in html
    assert '<time datetime="2024-01-31">31/01/2024</time>' in html

    from pathlib import Path

    from django.template.loader import get_template

    fonte = Path(get_template(TEMPLATE_HISTORICO).origin.name).read_text("utf-8")
    assert "autoescape" not in fonte and "|safe" not in fonte


@pytest.mark.spec("V8-OVL-105")
def test_acao_que_altera_estado_e_post_com_csrf(superusuario):
    url = "/v8/demo/clientes/arquivar/"
    cliente = cliente_http(superusuario, enforce_csrf_checks=True)

    assert cliente.get(url).status_code == 405
    assert cliente.get(url + "?ids=1").status_code == 405
    assert cliente.head(url).status_code == 405

    # Sem o token, o POST é recusado.
    assert cliente.post(url, {"ids": ["1"]}).status_code == 403

    pagina = html_de(cliente.get("/v8/demo/clientes/"))
    formulario = re.search(r'<form id="demo-arquivar".*?</form>', pagina, re.S).group(0)
    assert 'method="post"' in formulario and f'action="{url}"' in formulario
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', formulario).group(
        1
    )
    resposta = cliente.post(url, {"ids": ["1"], "csrfmiddlewaretoken": token})
    assert resposta.status_code == 302
    assert resposta["Location"] == "/v8/demo/clientes/"

    # Nenhuma rota do v8 dispensa o CSRF.
    import cmj.v8.urls

    for rota in cmj.v8.urls.urlpatterns:
        assert not getattr(rota.callback, "csrf_exempt", False), rota
        assert not getattr(rota.callback.view_class.dispatch, "csrf_exempt", False)


@pytest.mark.spec("V8-OVL-106")
def test_resposta_de_fragmento_leva_noindex(comum, superusuario):
    respostas = [
        cliente_http(superusuario).get(URL_DEMO_FRAGMENTO),
        cliente_http(superusuario).get("/v8/_frag/demo/cliente/999/historico/"),
        cliente_http(comum).get(URL_DEMO_FRAGMENTO),
        cliente_http().get(URL_DEMO_FRAGMENTO, headers=CABECALHOS_FRAGMENTO),
    ]
    assert [r.status_code for r in respostas] == [200, 404, 403, 401]
    for resposta in respostas:
        assert resposta["X-Robots-Tag"] == "noindex"


@pytest.mark.spec("V8-OVL-102")
def test_fragmento_que_depende_do_usuario_nao_usa_cache_compartilhado(superusuario):
    from pathlib import Path

    from django.template.loader import get_template

    pasta = Path(get_template(TEMPLATE_HISTORICO).origin.name).parents[1]
    assert pasta.name == "partials"
    fragmentos = sorted(pasta.rglob("*.html"))
    assert fragmentos
    # Nenhum fragmento atual usa {% cache %}. Quando um usar, a chave precisa
    # levar o usuário ou as permissões de que o conteúdo depende.
    for arquivo in fragmentos:
        assert "{% cache" not in arquivo.read_text(encoding="utf-8"), arquivo

    resposta = cliente_http(superusuario).get(URL_DEMO_FRAGMENTO)
    assert resposta["Cache-Control"] == "private"
    assert "Cookie" in resposta["Vary"]
