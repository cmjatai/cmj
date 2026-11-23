"""Testes da spec docs/specs/loa/listagem-emendas.md.

Cada teste está ligado a uma regra pelo marker ``spec``.
"""

import datetime
import io
import re
import zipfile
from decimal import Decimal
from unittest import mock
from urllib.parse import quote

import pymupdf
import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection
from django.template.loader import render_to_string
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from model_mommy import mommy

from cmj.loa.models import (
    AgrupamentoEmendaLoa,
    Despesa,
    EmendaLoa,
    EmendaLoaRegistroContabil,
    Entidade,
    Loa,
    OficioAjusteLoa,
    RegistroAjusteLoa,
    UnidadeOrcamentaria,
)
from cmj.loa.models.m_entidade import validar_cnpj_entidade
from cmj.loa.tests.conftest import _make_user
from cmj.loa.views.v_emendaloa import alinhar_valor
from cmj.mixins import GoogleRecapthaViewMixin
from cmj.utils.utils_report import make_pdf, pdf_base_url
from sapl.base.models import OperadorAutor
from sapl.materia.models import MateriaLegislativa
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Legislatura

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _sem_rede_social():
    """Gravar matéria dispara o envio ao Telegram, que nos testes roda na hora
    (task_always_eager) e fica esperando a rede."""
    with mock.patch("cmj.core.tasks.task_send_rede_social.apply_async"):
        yield


@pytest.fixture
def legislatura_atual(db):
    """O save() da emenda de LOA com matéria calcula disponibilidades pela
    legislatura atual."""
    return Legislatura.objects.create(
        numero=99,
        data_inicio=datetime.date(2025, 1, 1),
        data_fim=datetime.date(2028, 12, 31),
        data_eleicao=datetime.date(2024, 10, 6),
    )


def materia_da_loa(numero, ano, **kwargs):
    return mommy.make(
        MateriaLegislativa,
        numero=numero,
        ano=ano,
        data_apresentacao=datetime.date(2026, 9, 1),
        **kwargs,
    )


@pytest.fixture
def loa(legislatura_atual):
    """LOA com matéria já transformada em norma: a tela só abre com matéria
    (LOA-LST-087) e oferece as fases de 25 em diante (LOA-LST-024)."""
    materia = materia_da_loa(1000, 2026, em_tramitacao=False)
    mommy.make(NormaJuridica, materia=materia)
    return mommy.make(Loa, ano=2027, publicado=True, materia=materia)


ANEXO_LOCAL = '<link rel="attachment" href="file:///etc/hostname">'
TAG = '<b id="inj">X</b>'


def gerar_pdf_da_listagem(client, loa, query):
    """Gera o PDF da listagem e devolve (resposta, HTML enviado ao WeasyPrint)."""
    capturado = {}

    def _render(template_name, context=None, *args, **kwargs):
        html = render_to_string(template_name, context, *args, **kwargs)
        capturado["html"] = html
        return html

    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})
    with (
        mock.patch("cmj.loa.views.v_emendaloa.render_to_string", _render),
        recaptcha_valido(),
    ):
        # Anônimo passa pelo gate do reCAPTCHA (LOA-LST-085)
        response = client.post(f"{url}?pdf&{query}", {"g-recaptcha-response": "token"})
    return response, capturado.get("html", "")


def recaptcha_valido(valido=True):
    def _validar(self, request):
        if not valido:
            raise ValidationError("Ocorreu um erro na validação do reCAPTCHA.")
        return True

    return mock.patch.object(GoogleRecapthaViewMixin, "_validate_recaptcha", _validar)


def anexos(pdf_bytes):
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return doc.embfile_count()


@pytest.mark.spec("LOA-LST-049")
def test_pdf_anonimo_escapa_a_busca_por_termos(client, loa, make_emenda):
    make_emenda(fase=40)

    response, html = gerar_pdf_da_listagem(
        client, loa, "finalidade=" + quote(f"zz {TAG}{ANEXO_LOCAL}")
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert TAG not in html
    assert "&lt;b id=&quot;inj&quot;&gt;X&lt;/b&gt;" in html
    assert anexos(response.content) == 0


@pytest.mark.spec("LOA-LST-049")
def test_pdf_escapa_indicacao_e_finalidade_da_emenda(
    client, loa, parlamentar, make_emenda
):
    emenda = make_emenda(fase=40, parlamentar=parlamentar)
    # O save() recalcula a indicação e limpa a finalidade; update() grava o texto
    # cru, como faria um ponto de escrita que não passa pelo model.
    EmendaLoa.all_objects.all_objects().filter(pk=emenda.pk).update(
        indicacao=f"Indicação {TAG}",
        finalidade=f"Finalidade {ANEXO_LOCAL}",
    )

    response, html = gerar_pdf_da_listagem(client, loa, "fase=40")

    assert response.status_code == 200
    assert TAG not in html
    assert ANEXO_LOCAL not in html
    assert "Indicação &lt;b id=&quot;inj&quot;&gt;X&lt;/b&gt;" in html
    assert "Finalidade &lt;link rel=&quot;attachment&quot;" in html
    assert anexos(response.content) == 0


@pytest.mark.spec("LOA-LST-049")
def test_pdf_agrupado_escapa_titulo_do_grupo(client, loa, unidade, make_emenda):
    unidade.especificacao = f"Unidade {TAG}"
    unidade.save()
    make_emenda(fase=40)

    response, html = gerar_pdf_da_listagem(
        client,
        loa,
        "fase=40&agrupamento=despesa__unidade&tipo_agrupamento=sem_registro",
    )

    assert response.status_code == 200
    assert TAG not in html
    assert "Unidade &lt;b id=&quot;inj&quot;&gt;X&lt;/b&gt;" in html


def test_make_pdf_nao_busca_arquivo_local():
    html = f"<html><head>{ANEXO_LOCAL}</head><body>Teste</body></html>"

    pdf = make_pdf(base_url="http://testserver/", main_template=html)

    assert anexos(pdf) == 0


def test_make_pdf_continua_aceitando_data_uri():
    html = (
        '<html><head><link rel="attachment" '
        'href="data:text/plain;base64,b2k=" title="a.txt"></head>'
        "<body>Teste</body></html>"
    )

    pdf = make_pdf(base_url="http://testserver/", main_template=html)

    assert anexos(pdf) == 1


@pytest.mark.spec("LOA-LST-081")
def test_finalidade_ignora_marcador_fora_da_lista(make_emenda):
    dono = _make_user("dono_emenda")
    emenda = make_emenda(owner=dono, finalidade="Antes {owner__password} depois")

    assert emenda.finalidade_format == "Antes  depois."
    assert dono.password not in emenda.finalidade_format


@pytest.mark.spec("LOA-LST-081")
def test_finalidade_substitui_marcadores_permitidos(make_emenda):
    entidade = mommy.make(Entidade, nome_fantasia="Casa Abrigo")
    emenda = make_emenda(
        entidade=entidade,
        finalidade="Apoio à {entidade__nome_fantasia}",
    )

    assert emenda.finalidade_format == "Apoio à CASA ABRIGO."


@pytest.mark.spec("LOA-LST-019")
def test_zip_gera_os_pdfs_no_processo_sem_usar_o_host(
    client, loa, autor, parlamentar, make_emenda
):
    emenda = make_emenda(
        fase=EmendaLoa.LIBERACAO_CONTABIL, owner=autor, parlamentar=parlamentar
    )
    client.force_login(autor)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with (
        mock.patch("requests.get") as http_get,
        mock.patch(
            "cmj.utils.utils_report.make_pdf", return_value=b"%PDF-fake"
        ) as fake_pdf,
    ):
        response = client.get(f"{url}?zip", HTTP_HOST="10.0.0.99:6379")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/zip"
    http_get.assert_not_called()
    assert fake_pdf.call_args.kwargs["base_url"] == settings.BASE_URL
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        nomes = z.namelist()
        assert len(nomes) == 1
        assert str(emenda.id) in nomes[0]
        assert z.read(nomes[0]) == b"%PDF-fake"


@pytest.mark.spec("LOA-LST-019")
def test_zip_omite_emenda_cujo_pdf_falha_e_lista_no_leia_me(
    client, loa, autor, parlamentar, make_emenda
):
    emendas = {
        make_emenda(
            fase=EmendaLoa.LIBERACAO_CONTABIL, owner=autor, parlamentar=parlamentar
        ).id
        for _ in range(2)
    }
    client.force_login(autor)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with mock.patch(
        "cmj.utils.utils_report.make_pdf",
        side_effect=[RuntimeError("falha"), pdf_de_uma_pagina()],
    ):
        response = client.get(f"{url}?zip")

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        nomes = z.namelist()
        leia_me = z.read("LEIA-ME_emendas_nao_incluidas.txt").decode()
    (pdf,) = [n for n in nomes if n.endswith(".pdf")]
    incluida = int(pdf.split("_")[1])
    (omitida,) = emendas - {incluida}
    assert f"- Emenda {omitida} (" in leia_me
    assert f"Emenda {incluida} " not in leia_me


@pytest.mark.spec("LOA-LST-019")
def test_zip_sem_falha_nao_tem_leia_me(client, loa, autor, parlamentar, make_emenda):
    make_emenda(fase=EmendaLoa.LIBERACAO_CONTABIL, owner=autor, parlamentar=parlamentar)
    client.force_login(autor)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with mock.patch("cmj.utils.utils_report.make_pdf", pdf_de_uma_pagina):
        response = client.get(f"{url}?zip")

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        nomes = z.namelist()
    assert len(nomes) == 1 and nomes[0].endswith(".pdf")


def test_documento_pdf_numera_artigos_a_partir_de_1_em_cada_documento(make_emenda):
    emenda = make_emenda(fase=EmendaLoa.LIBERACAO_CONTABIL)
    htmls = []

    def _captura(base_url, main_template, **kwargs):
        htmls.append(main_template)
        return b""

    with mock.patch("cmj.utils.utils_report.make_pdf", _captura):
        EmendaLoa.service.documento_pdf(emenda, "http://testserver/")
        EmendaLoa.service.documento_pdf(emenda, "http://testserver/")

    assert "Art 1º" in htmls[0]
    assert htmls[0] == htmls[1]


# ------------------------------------------- visibilidade (LOA-LST-005 e 006)


@pytest.fixture
def loa_nao_publicada(legislatura_atual):
    # Matéria sem norma: o save() de emenda já gravada chama sync(), que lê
    # artigos de uma view SQL que não existe nos testes
    materia = materia_da_loa(1001, 2026)
    with mock.patch.object(
        EmendaLoa, "artigos", new_callable=mock.PropertyMock, return_value=[]
    ):
        yield mommy.make(Loa, ano=2028, publicado=False, materia=materia)


@pytest.fixture
def emenda_nao_publicada(loa_nao_publicada, make_emenda, autor, parlamentar):
    unidade = mommy.make(
        UnidadeOrcamentaria,
        loa=loa_nao_publicada,
        codigo="09",
        especificacao="Unidade 2030",
        recebe_emenda_impositiva=True,
    )
    loa_nao_publicada.parlamentares.add(parlamentar)
    return make_emenda(
        loa=loa_nao_publicada,
        unidade=unidade,
        fase=EmendaLoa.LIBERACAO_CONTABIL,
        owner=autor,
        parlamentar=parlamentar,
    )


def ids_na_listagem(client, loa):
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})
    response = client.get(url)
    assert response.status_code == 200
    return {e.id for e in response.context["object_list"]}


def status_da_listagem(client, loa_pk, query=""):
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa_pk})
    return client.get(f"{url}{query}").status_code


@pytest.mark.spec("LOA-LST-005")
@pytest.mark.parametrize("query", ["", "?pdf", "?zip", "?registrar"])
def test_anonimo_recebe_404_em_loa_nao_publicada(client, emenda_nao_publicada, query):
    # o 404 vem antes da verificação reCAPTCHA do PDF
    assert status_da_listagem(client, emenda_nao_publicada.loa_id, query) == 404


@pytest.mark.spec("LOA-LST-006")
def test_conta_comum_recebe_404_em_loa_nao_publicada(client, emenda_nao_publicada):
    client.force_login(_make_user("conta_comum"))

    assert status_da_listagem(client, emenda_nao_publicada.loa_id) == 404


@pytest.mark.spec("LOA-LST-006")
@pytest.mark.parametrize("perfil", ["autor_b", "editor_contabil", "superuser"])
def test_operador_e_contabilidade_veem_loa_nao_publicada(
    client, request, perfil, emenda_nao_publicada
):
    client.force_login(request.getfixturevalue(perfil))

    assert ids_na_listagem(client, emenda_nao_publicada.loa) == {
        emenda_nao_publicada.id
    }


@pytest.mark.spec("LOA-LST-006")
def test_operador_recebe_404_em_loa_nao_publicada_cuja_materia_virou_norma(
    client, autor_b, emenda_nao_publicada
):
    materia = mommy.make(MateriaLegislativa, numero=1, ano=2030)
    mommy.make(NormaJuridica, materia=materia)
    Loa.objects.filter(pk=emenda_nao_publicada.loa_id).update(materia=materia)
    client.force_login(autor_b)

    assert status_da_listagem(client, emenda_nao_publicada.loa_id) == 404


@pytest.mark.spec("LOA-LST-003")
def test_loa_inexistente_responde_404(client, loa):
    client.force_login(_make_user("superuser_loa_inexistente", is_superuser=True))

    assert status_da_listagem(client, loa.pk + 1000) == 404


@pytest.mark.spec("LOA-LST-006")
def test_qualquer_um_ve_todas_as_fases_de_loa_publicada(client, loa, make_emenda):
    emenda = make_emenda(fase=EmendaLoa.PROPOSTA_LIBERADA)

    assert ids_na_listagem(client, loa) == {emenda.id}


@pytest.mark.spec("LOA-LST-083")
def test_api_anonimo_nao_consulta_emenda_de_loa_nao_publicada(
    client, emenda_nao_publicada
):
    base = "/api/loa/emendaloa/"
    lista = client.get(base, {"loa": emenda_nao_publicada.loa_id})
    detalhe = client.get(f"{base}{emenda_nao_publicada.id}/")
    with mock.patch("cmj.utils.utils_report.make_pdf", return_value=b""):
        documento = client.get(f"{base}{emenda_nao_publicada.id}/view/")

    assert lista.status_code == 200
    assert emenda_nao_publicada.id not in [r["id"] for r in lista.json()["results"]]
    assert detalhe.status_code == 404
    assert documento.status_code == 404


@pytest.mark.spec("LOA-LST-083")
def test_api_operador_consulta_emenda_de_loa_nao_publicada(
    client, autor_b, emenda_nao_publicada
):
    client.force_login(autor_b)

    response = client.get(f"/api/loa/emendaloa/{emenda_nao_publicada.id}/")

    assert response.status_code == 200


def pdf_de_uma_pagina(*args, **kwargs):
    doc = pymupdf.Document()
    doc.new_page()
    return doc.tobytes()


@pytest.mark.spec("LOA-LST-017")
def test_registro_pela_listagem_gera_pdf_sem_http_em_loa_nao_publicada(
    emenda_nao_publicada,
):
    with (
        mock.patch("requests.get") as http_get,
        mock.patch("cmj.utils.utils_report.make_pdf", pdf_de_uma_pagina),
    ):
        arq_bytes, arq_name = emenda_nao_publicada.retrieve_file_bytes()

    http_get.assert_not_called()
    assert arq_bytes is not None
    assert arq_name == EmendaLoa.service.nome_documento(emenda_nao_publicada)


def registrar_pela_listagem(client, loa):
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})
    with mock.patch("cmj.loa.views.v_emendaloa.tasks") as tasks:
        response = client.post(url, {"registrar": "1"})
    disparou = (
        tasks.task_register_emendaloa_proposicao.apply_async.called
        or tasks.task_register_emendaloa_proposicao_function.called
    )
    return response, disparou


@pytest.mark.spec("LOA-LST-017")
@pytest.mark.parametrize("logado", [False, True])
def test_registro_recusado_volta_para_a_listagem_com_aviso(client, loa, logado):
    if logado:
        client.force_login(_make_user("conta_comum_registrar"))

    response, disparou = registrar_pela_listagem(client, loa)

    assert not disparou
    assert response.status_code == 302
    assert response.url == reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})
    avisos = [str(m) for m in response.wsgi_request._messages]
    assert avisos and avisos[0].startswith("Ação não permitida")


@pytest.mark.spec("LOA-LST-017")
@pytest.mark.parametrize("em_andamento", [False, True])
def test_registro_do_operador_vai_para_a_lista_de_proposicoes(
    client, loa, autor, make_emenda, em_andamento
):
    emenda = make_emenda(fase=EmendaLoa.LIBERACAO_CONTABIL, owner=autor)
    if em_andamento:
        EmendaLoa.all_objects.all_objects().filter(pk=emenda.pk).update(
            metadata={"register_emendaloa_proposicao_task": "em andamento"}
        )
    client.force_login(autor)

    response, disparou = registrar_pela_listagem(client, loa)

    assert disparou is not em_andamento
    assert response.status_code == 302
    assert response.url == reverse("sapl.materia:proposicao_list")


@pytest.mark.spec("LOA-LST-015")
def test_botoes_de_registro_consideram_as_emendas_dos_operadores_do_autor(
    client, loa, autor, autor_b, make_emenda
):
    colega = _make_user("colega_do_autor_a")
    mommy.make(OperadorAutor, user=colega, autor=autor.operadorautor_set.first().autor)
    make_emenda(fase=EmendaLoa.LIBERACAO_CONTABIL, owner=colega)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    client.force_login(autor)
    do_mesmo_autor = client.get(url).content.decode()
    client.force_login(autor_b)
    de_outro_autor = client.get(url).content.decode()

    assert 'name="registrar"' in do_mesmo_autor and "?zip" in do_mesmo_autor
    assert 'name="registrar"' not in de_outro_autor and "?zip" not in de_outro_autor


@pytest.mark.spec("LOA-LST-016")
def test_botao_de_registro_e_formulario_post_com_csrf(client, loa, autor, make_emenda):
    make_emenda(fase=EmendaLoa.LIBERACAO_CONTABIL, owner=autor)
    client.force_login(autor)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    html = client.get(url).content.decode()

    (form,) = re.findall(
        r"<form[^>]*form-register-emendas-liberadas[^>]*>.*?</form>", html, re.S
    )
    assert 'method="post"' in form and f'action="{url}"' in form
    assert 'name="csrfmiddlewaretoken"' in form
    assert 'name="registrar"' in form
    assert "?registrar" not in html


@pytest.mark.spec("LOA-LST-016")
def test_registro_por_get_responde_405_sem_registrar(client, loa, autor, make_emenda):
    make_emenda(fase=EmendaLoa.LIBERACAO_CONTABIL, owner=autor)
    client.force_login(autor)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with mock.patch("cmj.loa.views.v_emendaloa.tasks") as tasks:
        response = client.get(f"{url}?registrar")

    assert response.status_code == 405
    assert not tasks.mock_calls


@pytest.mark.spec("LOA-LST-016")
def test_registro_por_post_sem_csrf_e_recusado(loa, autor, make_emenda):
    make_emenda(fase=EmendaLoa.LIBERACAO_CONTABIL, owner=autor)
    client = Client(enforce_csrf_checks=True)
    client.force_login(autor)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with mock.patch("cmj.loa.views.v_emendaloa.tasks") as tasks:
        response = client.post(url, {"registrar": "1"})

    assert response.status_code == 403
    assert not tasks.mock_calls


@pytest.mark.spec("LOA-LST-016")
def test_post_sem_registrar_responde_405(client, loa):
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    assert client.post(url, {"outra": "1"}).status_code == 405


# ------------------------------------------------ reCAPTCHA no PDF (LOA-LST-085)


@pytest.mark.spec("LOA-LST-085")
def test_anonimo_recebe_gate_em_vez_do_pdf(client, loa, make_emenda):
    make_emenda(fase=40)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with mock.patch("cmj.utils.utils_report.make_pdf") as gerar:
        response = client.get(f"{url}?pdf&fase=40")

    assert response.status_code == 200
    assert "crud/gate.html" in [t.name for t in response.templates]
    assert response.context["form_action"] == f"{url}?pdf&fase=40"
    gerar.assert_not_called()


@pytest.mark.spec("LOA-LST-085")
def test_anonimo_com_recaptcha_invalido_volta_ao_gate(client, loa, make_emenda):
    make_emenda(fase=40)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with (
        recaptcha_valido(False),
        mock.patch("cmj.utils.utils_report.make_pdf") as gerar,
    ):
        response = client.post(f"{url}?pdf&fase=40", {"g-recaptcha-response": "x"})

    assert response.status_code == 200
    assert "crud/gate.html" in [t.name for t in response.templates]
    assert response.context["error"]
    gerar.assert_not_called()


@pytest.mark.spec("LOA-LST-085")
def test_anonimo_com_recaptcha_valido_recebe_pdf_com_os_filtros(
    client, loa, make_emenda
):
    make_emenda(fase=40, finalidade="Emenda na fase quarenta")
    make_emenda(fase=50, finalidade="Emenda na fase cinquenta")

    response, html = gerar_pdf_da_listagem(client, loa, "fase=40")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert "Emenda na fase quarenta" in html
    assert "Emenda na fase cinquenta" not in html


@pytest.mark.spec("LOA-LST-085")
def test_usuario_logado_gera_pdf_sem_gate(client, loa, make_emenda):
    make_emenda(fase=40)
    client.force_login(_make_user("conta_comum_pdf"))
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    response = client.get(f"{url}?pdf&fase=40")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


# -------------------------------------- base dos endereços do PDF (LOA-LST-086)

HOST_FORJADO = "10.0.0.99:6379"


def test_pdf_base_url_usa_base_url_e_mantem_o_caminho(rf):
    request = rf.get("/loa/1/emendaloa?pdf&fase=40", HTTP_HOST=HOST_FORJADO)

    base = pdf_base_url(request)

    assert base == settings.BASE_URL.rstrip("/") + "/loa/1/emendaloa?pdf&fase=40"
    assert HOST_FORJADO not in base


@pytest.mark.spec("LOA-LST-086")
def test_pdf_da_listagem_ignora_o_host_da_requisicao(client, loa, make_emenda):
    make_emenda(fase=40)
    client.force_login(_make_user("conta_comum_host"))
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with mock.patch(
        "cmj.loa.views.v_emendaloa.make_pdf", return_value=b"%PDF"
    ) as gerar:
        client.get(f"{url}?pdf&fase=40", HTTP_HOST=HOST_FORJADO)

    assert gerar.call_args.kwargs["base_url"].startswith(settings.BASE_URL.rstrip("/"))
    assert HOST_FORJADO not in gerar.call_args.kwargs["base_url"]


@pytest.mark.spec("LOA-LST-086")
def test_pdf_da_emenda_na_api_ignora_o_host_da_requisicao(client, make_emenda):
    emenda = make_emenda(fase=EmendaLoa.LIBERACAO_CONTABIL)

    with mock.patch(
        "cmj.utils.utils_report.make_pdf", side_effect=lambda **kw: pdf_de_uma_pagina()
    ) as gerar:
        response = client.get(
            f"/api/loa/emendaloa/{emenda.pk}/view/", HTTP_HOST=HOST_FORJADO
        )

    assert response.status_code == 200
    assert HOST_FORJADO not in gerar.call_args.kwargs["base_url"]


@pytest.mark.spec("LOA-LST-086")
def test_pdf_do_agrupamento_na_api_ignora_o_host_da_requisicao(
    client, editor_contabil, agrupamento, make_emenda
):
    for _ in range(2):
        el = make_emenda(fase=EmendaLoa.EDICAO_CONTABIL, permite_juncao_coletiva=True)
        AgrupamentoEmendaLoa.objects.create(agrupamento=agrupamento, emendaloa=el)
    client.force_login(editor_contabil)

    with mock.patch(
        "cmj.api.loa.views.agrupamento.make_pdf",
        side_effect=lambda **kw: pdf_de_uma_pagina(),
    ) as gerar:
        response = client.get(
            f"/api/loa/agrupamento/{agrupamento.pk}/view/?model=1",
            HTTP_HOST=HOST_FORJADO,
        )

    assert response.status_code == 200
    assert HOST_FORJADO not in gerar.call_args.kwargs["base_url"]


# ------------------------------------- soma das emendas do grupo (LOA-LST-055)


def registrar(emenda, unidade, *valores):
    for valor in valores:
        EmendaLoaRegistroContabil.objects.create(
            emendaloa=emenda,
            despesa=mommy.make(
                Despesa, loa=emenda.loa, unidade=unidade, _fill_optional=False
            ),
            valor=Decimal(valor),
        )


@pytest.mark.spec("LOA-LST-055")
def test_emenda_com_dois_registros_no_grupo_entra_uma_vez_na_soma_das_emendas(
    client, loa, unidade, make_emenda
):
    dois_registros = make_emenda(fase=40, valor=Decimal("200000.00"))
    registrar(dois_registros, unidade, "130000.00", "70000.00")
    um_registro = make_emenda(fase=40, valor=Decimal("98000.00"))
    registrar(um_registro, unidade, "98000.00")
    client.force_login(_make_user("conta_comum_soma"))
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    # O __str__ do registro lê a view SQL loa_despesa_consulta, que não existe
    # nos testes (--no-migrations)
    with (
        mock.patch.object(
            EmendaLoaRegistroContabil,
            "__str__",
            lambda rc: f"R$ {rc.str_valor} - despesa",
        ),
        mock.patch("cmj.loa.views.v_emendaloa.make_pdf", return_value=b"%PDF"),
        mock.patch(
            "cmj.loa.views.v_emendaloa.render_to_string", return_value=""
        ) as render,
    ):
        client.get(
            f"{url}?pdf&fase=40&agrupamento=despesa__unidade"
            "&tipo_agrupamento=insercao"
        )

    contexto = render.call_args.args[1]
    (grupo,) = contexto["groups"]
    assert len(grupo["rows"]) == 2
    assert grupo["sub_total_emendas"] == "298.000,00"
    assert grupo["sub_total_agrupado"] == "298.000,00"


# ------------------------------------------------ Total do PDF (LOA-LST-062)


def contexto_do_pdf(client, loa, query):
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})
    # O __str__ do registro lê a view SQL loa_despesa_consulta, que não existe
    # nos testes (--no-migrations)
    with (
        mock.patch.object(
            EmendaLoaRegistroContabil,
            "__str__",
            lambda rc: f"R$ {rc.str_valor} - despesa",
        ),
        mock.patch("cmj.loa.views.v_emendaloa.make_pdf", return_value=b"%PDF"),
        mock.patch(
            "cmj.loa.views.v_emendaloa.render_to_string", return_value=""
        ) as render,
    ):
        client.get(f"{url}?pdf&{query}")
    return render.call_args.args[1]


@pytest.mark.spec("LOA-LST-062")
@pytest.mark.parametrize("via,sinal", [("insercao", ""), ("deducao", "-")])
def test_total_soma_cada_emenda_uma_vez_e_e_positivo(
    client, loa, unidade, make_emenda, via, sinal
):
    outra = mommy.make(
        UnidadeOrcamentaria, loa=loa, codigo="02", especificacao="Outra Unidade"
    )
    em_dois_grupos = make_emenda(fase=40, valor=Decimal("100.00"))
    registrar(em_dois_grupos, unidade, f"{sinal}60.00")
    registrar(em_dois_grupos, outra, f"{sinal}40.00")
    em_um_grupo = make_emenda(fase=40, valor=Decimal("50.00"))
    registrar(em_um_grupo, unidade, f"{sinal}50.00")
    client.force_login(_make_user("conta_comum_total"))

    contexto = contexto_do_pdf(
        client, loa, f"fase=40&agrupamento=despesa__unidade&tipo_agrupamento={via}"
    )

    assert len(contexto["groups"]) == 2
    assert contexto["total"] == "150,00"


# ------------------------------------------ filtros aplicados (LOA-LST-047)


@pytest.mark.spec("LOA-LST-047")
def test_pdf_informa_entidade_unidade_autoria_e_indicacao(
    client, loa, unidade, parlamentar, make_emenda
):
    entidade = mommy.make(Entidade, nome_fantasia="Casa Abrigo", ativo=True)
    emenda = make_emenda(fase=40, entidade=entidade, parlamentar=parlamentar)
    client.force_login(_make_user("conta_comum_filtros"))

    contexto = contexto_do_pdf(
        client,
        loa,
        f"entidade={entidade.pk}&unidade={unidade.pk}&autoria=individual"
        f"&indicacao={quote(emenda.indicacao)}",
    )

    filtros = contexto["filters"]
    assert "<strong>Entidade:</strong> Casa Abrigo" in filtros
    assert f"<strong>Unidade Orçamentária:</strong> {unidade}" in filtros
    assert "<strong>Autoria:</strong> Individual" in filtros
    assert f"<strong>Indicação:</strong> {emenda.indicacao}" in filtros
    assert len(contexto["groups"][0]["rows"]) == 1


@pytest.mark.spec("LOA-LST-047")
def test_pdf_nao_informa_autoria_ambas(client, loa, make_emenda):
    make_emenda(fase=40)
    client.force_login(_make_user("conta_comum_ambas"))

    contexto = contexto_do_pdf(client, loa, "fase=40&autoria=ambas")

    assert "Autoria" not in contexto["filters"]


# ------------------------------- emenda sem unidade ou entidade (LOA-LST-057)


def titulos(contexto):
    """Linhas do título de cada grupo, como "código|especificação"."""
    return [
        [
            re.sub(r"<.*?>|&nbsp;", "", linha).replace(" - ", "|").strip()
            for linha in g["title"].split("<br>")
        ]
        for g in contexto["groups"]
    ]


@pytest.mark.spec("LOA-LST-057")
def test_emenda_sem_unidade_vai_para_grupo_sem_unidade_no_fim(client, loa, make_emenda):
    make_emenda(fase=40, valor=Decimal("10.00"))
    sem_unidade = make_emenda(fase=40, valor=Decimal("5.00"))
    EmendaLoa.all_objects.all_objects().filter(pk=sem_unidade.pk).update(unidade=None)
    client.force_login(_make_user("conta_comum_sem_unidade"))

    contexto = contexto_do_pdf(
        client,
        loa,
        "fase=40&agrupamento=despesa__unidade&tipo_agrupamento=sem_registro",
    )

    assert titulos(contexto) == [["01|Unidade Teste"], ["|Sem unidade orçamentária"]]
    assert contexto["total"] == "15,00"


@pytest.mark.spec("LOA-LST-057")
def test_emenda_sem_entidade_aparece_no_pdf_totalizado_so_por_entidade(
    client, loa, make_emenda
):
    entidade = mommy.make(Entidade, nome_fantasia="Casa Abrigo", cnes="123")
    make_emenda(fase=40, valor=Decimal("10.00"), entidade=entidade)
    make_emenda(fase=40, valor=Decimal("5.00"))
    client.force_login(_make_user("conta_comum_sem_entidade"))

    contexto = contexto_do_pdf(
        client, loa, "fase=40&agrupamento=entidade&tipo_agrupamento=sem_registro"
    )

    assert titulos(contexto) == [["123|Casa Abrigo"], ["|Sem entidade"]]
    assert contexto["total"] == "15,00"


@pytest.mark.spec("LOA-LST-060")
def test_emenda_lista_todos_os_seus_registros_nao_so_os_do_grupo(
    client, loa, unidade, make_emenda
):
    origem = mommy.make(
        UnidadeOrcamentaria, loa=loa, codigo="02", especificacao="Unidade Origem"
    )
    emenda = make_emenda(fase=40, valor=Decimal("10.00"))
    registrar(emenda, unidade, "10.00")
    registrar(emenda, origem, "-10.00")
    client.force_login(_make_user("conta_comum_todos_registros"))

    contexto = contexto_do_pdf(
        client,
        loa,
        "fase=40&agrupamento=despesa__unidade&tipo_agrupamento=insercao",
    )

    assert titulos(contexto) == [["01|Unidade Teste"]]
    (linha,) = contexto["groups"][0]["rows"]
    descricao = linha[0][0]
    assert "ORIGEM(-) E DESTINO(+)" in descricao
    assert descricao.count("<li>") == 2
    assert "-10,00" in descricao and "+10,00" in descricao


def com_ajuste_tecnico(emenda):
    # O hook de busca de RegistroAjusteLoa lê o M2M antes de haver pk; por isso o
    # primeiro save é sem atualizar a busca.
    ajuste = mommy.prepare(
        RegistroAjusteLoa,
        numero=1,
        ano=emenda.loa.ano,
        oficio_ajuste_loa=mommy.make(OficioAjusteLoa, loa=emenda.loa),
    )
    ajuste.save(auto_update_search=False)
    ajuste.emendaloa.add(emenda)
    return emenda


def linhas_do_pdf(contexto):
    """Descrição de cada emenda do PDF, pelo id do link para o detalhe."""
    linhas = {}
    for g in contexto["groups"]:
        for cols in g["rows"]:
            descricao = cols[0][0]
            pk = int(re.search(r"/emendaloa/(\d+)", descricao).group(1))
            linhas[pk] = descricao
    return linhas


@pytest.mark.spec("LOA-LST-089")
@pytest.mark.parametrize(
    "query", ["", "&agrupamento=despesa__unidade&tipo_agrupamento=sem_registro"]
)
def test_pdf_sinaliza_ajuste_e_impedimento_tecnico_e_mantem_valor_original(
    client, loa, make_emenda, query
):
    ajustada = com_ajuste_tecnico(make_emenda(fase=50, valor=Decimal("10.00")))
    impedida = make_emenda(fase=40, valor=Decimal("20.00"))
    normal = make_emenda(fase=50, valor=Decimal("30.00"))
    client.force_login(_make_user("conta_comum_ajuste_pdf"))

    contexto = contexto_do_pdf(client, loa, f"fase=40&fase=50{query}")

    linhas = linhas_do_pdf(contexto)
    assert "Possui ajuste técnico" in linhas[ajustada.id]
    assert "Em impedimento técnico" in linhas[impedida.id]
    assert "aviso-ajuste" not in linhas[normal.id]
    assert contexto["total"] == "60,00"


@pytest.mark.spec("LOA-LST-080")
def test_pdf_sem_resultado_tem_titulo_sem_marcador(client, loa, make_emenda):
    make_emenda(fase=40)
    client.force_login(_make_user("conta_comum_pdf_vazio"))

    contexto = contexto_do_pdf(client, loa, "fase=50")

    assert contexto["groups"] == []
    assert "{}" not in contexto["title"]
    assert contexto["title"].startswith("Listagem Geral das Emendas")


def alinhamento_antigo(texto, largura):
    # o laço que alinhar_valor substituiu; só termina se houver espaço no texto
    while len(texto) < largura:
        texto = texto.replace(" ", "  ", 1)
    return texto


@pytest.mark.spec("LOA-LST-060")
@pytest.mark.parametrize(
    "texto", ["R$ +1.000,00", "R$ -150.000,00", "R$ +0,50", "R$  +1,00 x"]
)
def test_alinhar_valor_da_o_mesmo_texto_do_alinhamento_antigo(texto):
    for largura in range(len(texto), len(texto) + 8):
        assert alinhar_valor(texto, largura) == alinhamento_antigo(texto, largura)


@pytest.mark.spec("LOA-LST-060")
def test_alinhar_valor_sem_espaco_alinha_o_texto_inteiro():
    assert alinhar_valor("+1,00", 8) == "   +1,00"
    assert alinhar_valor("+1.000,00", 5) == "+1.000,00"


@pytest.mark.spec("LOA-LST-061")
@pytest.mark.parametrize("via, calcula", [("sem_registro", False), ("insercao", True)])
def test_orcamento_do_grupo_so_e_calculado_nas_vias_com_registro(
    client, loa, unidade, make_emenda, via, calcula
):
    emenda = make_emenda(fase=40, valor=Decimal("10.00"))
    registrar(emenda, unidade, "10.00")
    client.force_login(_make_user(f"conta_comum_orcamento_{via}"))

    with CaptureQueriesContext(connection) as consultas:
        contexto = contexto_do_pdf(
            client,
            loa,
            f"fase=40&agrupamento=despesa__unidade&tipo_agrupamento={via}",
        )

    assert len(contexto["groups"]) == 1
    # orçamento original e movimentação geral são as únicas agregações do grupo
    agregacoes = [
        q["sql"]
        for q in consultas.captured_queries
        if q["sql"].startswith("SELECT SUM(")
    ]
    assert len(agregacoes) == (2 if calcula else 0)


@pytest.mark.spec("LOA-LST-058")
def test_grupo_com_dimensao_vazia_vai_para_o_fim(client, loa, unidade, make_emenda):
    entidade = mommy.make(Entidade, nome_fantasia="Zeta", cnes="9")
    make_emenda(fase=40)
    make_emenda(fase=40, entidade=entidade)
    client.force_login(_make_user("conta_comum_ordem"))

    contexto = contexto_do_pdf(
        client,
        loa,
        "fase=40&agrupamento=despesa__unidade&agrupamento=entidade"
        "&tipo_agrupamento=sem_registro",
    )

    assert titulos(contexto) == [
        ["01|Unidade Teste", "9|Zeta"],
        ["01|Unidade Teste", "|Sem entidade"],
    ]


# ---------------------------------------- cache do cartão (LOA-LST-040 e 041)


@pytest.fixture
def cache_em_memoria(settings):
    from django.core.cache import cache

    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
    cache.clear()
    return cache


def chave_do_cartao(emenda, logado):
    from django.core.cache.utils import make_template_fragment_key

    return make_template_fragment_key("l.el.l", [emenda.id, logado])


def chaves_do_cartao(emenda):
    """As duas versões do cartão: usuário logado e anônimo (LOA-LST-040)."""
    return [chave_do_cartao(emenda, True), chave_do_cartao(emenda, False)]


@pytest.mark.spec("LOA-LST-041")
def test_cartao_e_renovado_por_tramitacao_da_materia(cache_em_memoria, make_emenda):
    from sapl.materia.models import Tramitacao

    materia = mommy.make(MateriaLegislativa, numero=7, ano=2027)
    emenda = make_emenda(fase=40, materia=materia)
    # Status e unidades da tramitação são gravados antes do cache: o código
    # antigo apagava a chave pelo id de qualquer objeto salvo
    tramitacao = mommy.prepare(Tramitacao, materia=materia, _save_related=True)
    tramitacao.id = emenda.id + 1000
    cache_em_memoria.set_many({k: "cartão antigo" for k in chaves_do_cartao(emenda)})

    tramitacao.save()

    assert cache_em_memoria.get_many(chaves_do_cartao(emenda)) == {}


@pytest.mark.spec("LOA-LST-041")
def test_cartao_e_renovado_por_empenho_entidade_e_parlamentar(
    cache_em_memoria, make_emenda, parlamentar
):
    from cmj.loa.models import Empenho, EmpenhoEmendaAjuste

    entidade = mommy.make(Entidade, nome_fantasia="Casa Abrigo")
    emenda = make_emenda(fase=40, entidade=entidade, parlamentar=parlamentar)
    empenho = mommy.make(Empenho, _fill_optional=False)
    EmpenhoEmendaAjuste.objects.create(emendaloa=emenda, empenho=empenho)

    for objeto in (empenho, entidade, parlamentar):
        cache_em_memoria.set_many(
            {k: "cartão antigo" for k in chaves_do_cartao(emenda)}
        )
        objeto.save()
        assert cache_em_memoria.get_many(chaves_do_cartao(emenda)) == {}, objeto


@pytest.mark.spec("LOA-LST-041")
def test_model_sem_relacao_nao_apaga_cartao_de_emenda_com_o_mesmo_id(
    cache_em_memoria, make_emenda
):
    emenda = make_emenda(fase=40)
    outra = mommy.make(Entidade, nome_fantasia="Sem emendas")
    Entidade.objects.filter(pk=outra.pk).update(id=emenda.id)
    outra = Entidade.objects.get(pk=emenda.id)
    cache_em_memoria.set_many({k: "cartão vigente" for k in chaves_do_cartao(emenda)})

    outra.save()

    assert len(cache_em_memoria.get_many(chaves_do_cartao(emenda))) == 2


@pytest.mark.spec("LOA-LST-040")
def test_cartao_fica_em_cache_por_um_dia(
    client, settings, cache_em_memoria, loa, make_emenda
):
    import time

    settings.DEBUG = False
    materia = mommy.make(MateriaLegislativa, numero=8, ano=2027)
    emenda = make_emenda(fase=40, materia=materia)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    response = client.get(url)

    assert response.status_code == 200
    expira = cache_em_memoria._expire_info[
        cache_em_memoria.make_key(chave_do_cartao(emenda, logado=False))
    ]
    assert 86400 - 60 < expira - time.time() <= 86400


@pytest.mark.spec("LOA-LST-040")
def test_anonimo_nao_ve_selo_guardado_por_usuario_logado(
    client, settings, cache_em_memoria, loa, parlamentar, make_emenda
):
    settings.DEBUG = False
    materia = mommy.make(MateriaLegislativa, numero=9, ano=2027)
    make_emenda(
        fase=EmendaLoa.LIBERACAO_CONTABIL,
        materia=materia,
        parlamentar=parlamentar,
        permite_juncao_coletiva=False,
    )
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    client.force_login(_make_user("conta_comum_selo"))
    logado = client.get(url).content.decode()
    client.logout()
    anonimo = client.get(url).content.decode()

    assert "Emenda Individual" in logado
    assert "Emenda Individual" not in anonimo


# ------------------------------- matéria da LOA e filtros (LOA-LST-024/025/087)


@pytest.mark.spec("LOA-LST-087")
@pytest.mark.parametrize("query", ["", "?pdf", "?zip"])
def test_loa_sem_materia_nao_abre_a_listagem(client, query):
    sem_materia = mommy.make(Loa, ano=2029, publicado=True)
    client.force_login(_make_user("superuser_sem_materia", is_superuser=True))
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": sem_materia.pk})

    response = client.get(f"{url}{query}")

    assert response.status_code == 404


def fases_oferecidas(client, loa):
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})
    response = client.get(url)
    return [
        valor for valor, _ in response.context["filter"].form.fields["fase"].choices
    ]


@pytest.mark.spec("LOA-LST-024")
def test_loa_com_norma_oferece_fases_de_25_em_diante(client, loa):
    assert fases_oferecidas(client, loa) == [25, 30, 40, 50, 60, 99]


@pytest.mark.spec("LOA-LST-024")
def test_loa_sem_norma_oferece_fases_ate_20(client, loa_nao_publicada):
    client.force_login(_make_user("superuser_fases", is_superuser=True))

    assert fases_oferecidas(client, loa_nao_publicada) == [10, 12, 15, 17, 20]


@pytest.mark.spec("LOA-LST-066")
def test_formulario_tem_um_unico_botao_filtrar_para_o_script(client, loa):
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    html = client.get(url).content.decode()

    botoes = re.findall(r"<button[^>]*btn-filtrar[^>]*>\s*([^<]*?)\s*<", html)
    assert botoes == ["Filtrar"]
    # o script acha o filtro por esta classe, e não o formulário de registro
    (filtro,) = re.findall(r"<form[^>]*form-filter-emendaloa[^>]*>", html)
    assert 'method="get"' in filtro.lower()


@pytest.mark.spec("LOA-LST-071")
def test_gerar_pdf_abre_em_nova_aba(client, loa):
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    html = client.get(url).content.decode()

    (botao,) = re.findall(r'<input[^>]*name="pdf"[^>]*>', html)
    assert 'formtarget="_blank"' in botao


@pytest.mark.spec("LOA-LST-025")
def test_filtro_invalido_e_ignorado_com_aviso_no_campo(client, loa, make_emenda):
    saude = make_emenda(fase=40, tipo=EmendaLoa.SAUDE)
    make_emenda(fase=50, tipo=EmendaLoa.DIVERSOS)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    response = client.get(url, {"fase": "10", "tipo": EmendaLoa.SAUDE})

    assert [e.id for e in response.context["object_list"]] == [saude.id]
    assert "fase" in response.context["filter"].form.errors


@pytest.mark.spec("LOA-LST-025")
def test_pdf_com_filtro_invalido_mostra_a_tela_com_aviso(client, loa, make_emenda):
    make_emenda(fase=40)
    client.force_login(_make_user("conta_comum_pdf_invalido"))
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with mock.patch("cmj.loa.views.v_emendaloa.make_pdf") as gerar:
        response = client.get(f"{url}?pdf&fase=10")

    gerar.assert_not_called()
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/html")
    assert "fase" in response.context["filter"].form.errors
    assert "Há filtros inválidos" in response.content.decode()


# ------------------------------- combinações de totalização inválidas (LOA-LST-088)


@pytest.mark.spec("LOA-LST-088")
@pytest.mark.parametrize(
    "query, campo",
    [
        ("agrupamento=entidade&tipo_agrupamento=insercao", "agrupamento"),
        ("agrupamento=entidade&tipo_agrupamento=deducao", "agrupamento"),
        ("agrupamento=despesa__unidade", "tipo_agrupamento"),
        (
            "agrupamento=despesa__orgao&agrupamento=despesa__unidade"
            "&tipo_agrupamento=sem_registro",
            "agrupamento",
        ),
    ],
)
def test_pdf_com_totalizacao_invalida_mostra_a_tela_com_erro_no_campo(
    client, loa, make_emenda, query, campo
):
    make_emenda(fase=40)
    client.force_login(_make_user("conta_comum_totalizacao_invalida"))
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with mock.patch("cmj.loa.views.v_emendaloa.make_pdf") as gerar:
        response = client.get(f"{url}?pdf&fase=40&{query}")

    gerar.assert_not_called()
    assert response["Content-Type"].startswith("text/html")
    assert list(response.context["filter"].form.errors) == [campo]
    assert "Há filtros inválidos" in response.content.decode()
    # os campos de totalização não filtram: a lista segue com os demais filtros
    assert len(response.context["object_list"]) == 1


@pytest.mark.spec("LOA-LST-088")
@pytest.mark.parametrize(
    "query",
    [
        "agrupamento=despesa__unidade&agrupamento=entidade&tipo_agrupamento=sem_registro",
        "agrupamento=despesa__orgao&agrupamento=despesa__unidade&tipo_agrupamento=insercao",
        "tipo_agrupamento=deducao",
    ],
)
def test_totalizacao_valida_nao_tem_erro(client, loa, make_emenda, query):
    make_emenda(fase=40)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    response = client.get(f"{url}?fase=40&{query}")

    assert response.context["filter"].form.errors == {}


# ------------------------------------------- erro ao gerar o PDF (LOA-LST-046)


@pytest.mark.spec("LOA-LST-046")
@pytest.mark.parametrize(
    "onde",
    [
        "cmj.loa.views.v_emendaloa.EmendaLoaCrud.ListView.get_context_data_makepdf",
        "cmj.loa.views.v_emendaloa.make_pdf",
    ],
)
def test_erro_no_pdf_volta_para_a_tela_com_aviso_e_registra_a_causa(
    client, loa, make_emenda, onde
):
    make_emenda(fase=40)
    client.force_login(_make_user("conta_comum_erro_pdf"))
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    with (
        mock.patch(onde, side_effect=RuntimeError("causa do erro")),
        mock.patch("cmj.loa.views.v_emendaloa.logger") as logger,
    ):
        response = client.get(f"{url}?pdf&fase=40")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/html")
    assert "Não foi possível gerar o PDF" in response.content.decode()
    assert len(response.context["object_list"]) == 1
    # logger.exception registra a mensagem e o traceback da causa
    (mensagem,) = logger.exception.call_args.args
    assert f"LOA {loa.id}" in mensagem
    assert "fase=40" in mensagem


# ------------------------------------------ entidade só com CNPJ (LOA-LST-090)

CNPJ_VALIDO = "11.222.333/0001-81"
CPF_VALIDO = "529.982.247-25"


@pytest.mark.spec("LOA-LST-090")
@pytest.mark.parametrize(
    "valor",
    [CNPJ_VALIDO, "11222333000181", "0000" + "11222333000181", "", None, "0" * 18],
)
def test_entidade_aceita_cnpj_valido_ou_vazio(valor):
    validar_cnpj_entidade(valor)


@pytest.mark.spec("LOA-LST-090")
@pytest.mark.parametrize(
    "valor", [CPF_VALIDO, "52998224725", "11.222.333/0001-82", "CNPJ 11222333000181"]
)
def test_entidade_recusa_cpf_e_cnpj_invalido(valor):
    with pytest.raises(ValidationError):
        validar_cnpj_entidade(valor)


@pytest.mark.spec("LOA-LST-090")
def test_formulario_da_entidade_recusa_cpf():
    entidade = Entidade(
        nome_fantasia="Pessoa", razao_social="Pessoa", cpfcnpj=CPF_VALIDO
    )

    with pytest.raises(ValidationError) as erro:
        entidade.full_clean()

    assert "cpfcnpj" in erro.value.message_dict


@pytest.mark.spec("LOA-LST-090")
def test_api_recusa_entidade_com_cpf(api):
    cliente = api(_make_user("superuser_entidade_cpf", is_superuser=True))
    dados = {"nome_fantasia": "Pessoa", "razao_social": "Pessoa", "ativo": True}

    com_cpf = cliente.post("/api/loa/entidade/", {**dados, "cpfcnpj": CPF_VALIDO})
    com_cnpj = cliente.post("/api/loa/entidade/", {**dados, "cpfcnpj": CNPJ_VALIDO})

    assert com_cpf.status_code == 400 and "cpfcnpj" in com_cpf.json()
    assert com_cnpj.status_code == 201


@pytest.mark.spec("LOA-LST-090")
def test_cartao_rotula_o_numero_como_cnpj(client, loa, make_emenda):
    entidade = mommy.make(Entidade, nome_fantasia="Casa", cpfcnpj=CNPJ_VALIDO, cnes="")
    make_emenda(fase=40, entidade=entidade)
    url = reverse("cmj.loa:emendaloa_list", kwargs={"pk": loa.pk})

    html = client.get(url).content.decode()

    assert f"<strong>CNPJ:</strong> {CNPJ_VALIDO}" in html
    assert "CPF/CNPJ" not in html


# ---------------------------- campos internos da emenda na API (LOA-LST-091)

CAMPOS_INTERNOS = {"owner", "metadata", "search"}


def campos_da_api(client, emenda):
    detalhe = client.get(f"/api/loa/emendaloa/{emenda.id}/").json()
    (na_lista,) = [
        r
        for r in client.get("/api/loa/emendaloa/", {"loa": emenda.loa_id}).json()[
            "results"
        ]
        if r["id"] == emenda.id
    ]
    return set(detalhe), set(na_lista)


@pytest.mark.spec("LOA-LST-091")
@pytest.mark.parametrize("perfil", [None, "conta_comum", "autor_b"])
def test_api_oculta_campos_internos_de_quem_nao_edita(
    client, request, loa, autor, make_emenda, perfil
):
    emenda = make_emenda(fase=40, owner=autor)
    if perfil == "conta_comum":
        client.force_login(_make_user("conta_comum_api"))
    elif perfil:
        client.force_login(request.getfixturevalue(perfil))

    for campos in campos_da_api(client, emenda):
        assert not campos & CAMPOS_INTERNOS
        assert "finalidade" in campos


@pytest.mark.spec("LOA-LST-091")
@pytest.mark.parametrize("perfil", ["autor", "editor_contabil", "superuser"])
def test_api_mostra_campos_internos_a_quem_edita(
    client, request, loa, autor, make_emenda, perfil
):
    emenda = make_emenda(fase=40, owner=autor)
    client.force_login(request.getfixturevalue(perfil))

    for campos in campos_da_api(client, emenda):
        assert {"metadata", "search"} <= campos
        # `owner` segue a regra geral da API: só para quem lista o model
        assert ("owner" in campos) == (perfil == "superuser")


@pytest.mark.spec("LOA-LST-091")
def test_busca_da_api_oculta_campos_internos_do_anonimo(
    client, loa, autor, make_emenda
):
    emenda = make_emenda(fase=EmendaLoa.PROPOSTA, owner=autor)

    resultados = client.get(
        "/api/loa/emendaloa/search/", {"ano": loa.ano, "q": ""}
    ).json()["results"]

    (encontrada,) = [r for r in resultados if r["id"] == emenda.id]
    assert not set(encontrada) & CAMPOS_INTERNOS


def ids_da_api(client, loa, **params):
    resultados = client.get("/api/loa/emendaloa/", {"loa": loa.id, **params}).json()
    return [r["id"] for r in resultados["results"]]


@pytest.mark.spec("API-FIL-022")
@pytest.mark.parametrize("perfil", [None, "conta_comum"])
def test_api_ignora_filtro_e_ordenacao_por_campo_interno_de_quem_nao_o_ve(
    client, loa, autor, autor_b, make_emenda, perfil
):
    primeira = make_emenda(fase=40, owner=autor_b)
    segunda = make_emenda(fase=40, owner=autor)
    if perfil:
        client.force_login(_make_user("conta_comum_api"))
    padrao = ids_da_api(client, loa)
    assert sorted(padrao) == sorted([primeira.id, segunda.id])

    assert ids_da_api(client, loa, owner=autor.id) == padrao
    assert ids_da_api(client, loa, search__icontains="zzz") == padrao
    assert ids_da_api(client, loa, o="-owner") == padrao


@pytest.mark.spec("API-FIL-022")
def test_api_filtra_por_campo_interno_para_quem_o_ve(
    client, loa, autor, autor_b, make_emenda, superuser
):
    make_emenda(fase=40, owner=autor_b)
    segunda = make_emenda(fase=40, owner=autor)
    client.force_login(superuser)

    assert ids_da_api(client, loa, owner=autor.id) == [segunda.id]
