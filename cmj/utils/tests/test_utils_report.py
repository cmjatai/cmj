"""PDFs fora da LOA: base dos endereços relativos (LOA-LST-086) e protocolos
que o HTML pode buscar (LOA-LST-082).

Cada gerador de PDF deve usar ``pdf_base_url``: o caminho da página no domínio
de ``settings.BASE_URL``, nunca o ``Host`` da requisição. E só busca recursos
por http, https e data:.
"""

from unittest import mock

import pymupdf
import pytest
from django.conf import settings

from cmj.core.views import CertidaoPublicacaoCrud
from cmj.mixins import MultiFormatOutputMixin, PdfOutputMixin
from cmj.utils import utils_report
from sapl.relatorios.view_reports.mixins import RelatorioMixin

pytestmark = pytest.mark.django_db

HOST_FORJADO = "10.0.0.99:6379"
CAMINHO = "/relatorio/teste?pdf"
BASE_ESPERADA = settings.BASE_URL.rstrip("/") + CAMINHO


@pytest.fixture
def requisicao(rf):
    return rf.get(CAMINHO, HTTP_HOST=HOST_FORJADO)


@pytest.mark.spec("LOA-LST-086")
def test_render_pdf_to_response_usa_base_url(requisicao):
    template = mock.Mock(render=mock.Mock(return_value="<html></html>"))
    html = mock.Mock(return_value=mock.Mock(write_pdf=mock.Mock(return_value=b"%PDF")))

    with (
        mock.patch.object(utils_report.loader, "get_template", return_value=template),
        mock.patch.object(utils_report, "HTML", html),
    ):
        utils_report.render_pdf_to_response(requisicao, {}, "qualquer.html")

    assert html.call_args.kwargs["base_url"] == BASE_ESPERADA


@pytest.mark.spec("LOA-LST-086")
def test_pdf_output_mixin_usa_base_url(requisicao):
    class View(PdfOutputMixin):
        template_name = "qualquer.html"
        kwargs = {}

        def get_context_data(self):
            return {}

    view = View()
    view.request = requisicao

    with (
        mock.patch("cmj.mixins.render_to_string", return_value="<html></html>"),
        mock.patch("cmj.mixins.make_pdf", return_value=b"%PDF") as gerar,
    ):
        view.render_to_response({})

    assert gerar.call_args.kwargs["base_url"] == BASE_ESPERADA


@pytest.mark.spec("LOA-LST-086")
def test_multi_format_output_mixin_usa_base_url(requisicao):
    view = MultiFormatOutputMixin()
    view.request = requisicao

    with (
        mock.patch.object(
            MultiFormatOutputMixin,
            "get_template_pdf",
            return_value="x.html",
            create=True,
        ),
        mock.patch.object(MultiFormatOutputMixin, "to_json", return_value=None),
        mock.patch("cmj.mixins.render_to_string", return_value="<html></html>"),
        mock.patch("cmj.mixins.make_pdf", return_value=b"%PDF") as gerar,
    ):
        view.render_to_pdf({})

    assert gerar.call_args.kwargs["base_url"] == BASE_ESPERADA


@pytest.mark.spec("LOA-LST-086")
def test_relatorio_mixin_usa_base_url(requisicao):
    class View(RelatorioMixin):
        def get_template_pdf(self):
            return "qualquer.html"

    with (
        mock.patch(
            "sapl.relatorios.view_reports.mixins.render_to_string",
            return_value="<html></html>",
        ),
        mock.patch(
            "sapl.relatorios.view_reports.mixins.make_pdf", return_value=b"%PDF"
        ) as gerar,
    ):
        View().export_pdf(requisicao, {})

    assert gerar.call_args.kwargs["base_url"] == BASE_ESPERADA


# ------------------------- protocolos permitidos em todo PDF (LOA-LST-082)

ANEXO_LOCAL = '<link rel="attachment" href="file:///etc/hostname">'
HTML_COM_ANEXO_LOCAL = f"<html><head>{ANEXO_LOCAL}</head><body>Teste</body></html>"


def anexos(pdf_bytes):
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return doc.embfile_count()


@pytest.mark.spec("LOA-LST-082")
def test_render_pdf_to_response_nao_busca_arquivo_local(requisicao):
    template = mock.Mock(render=mock.Mock(return_value=HTML_COM_ANEXO_LOCAL))

    with mock.patch.object(utils_report.loader, "get_template", return_value=template):
        response = utils_report.render_pdf_to_response(requisicao, {}, "x.html")

    assert anexos(response.content) == 0


@pytest.mark.spec("LOA-LST-082")
def test_certidao_de_publicacao_nao_busca_arquivo_local(requisicao):
    view = mock.Mock(object=mock.Mock(certificado=None, id=1))

    with mock.patch(
        "cmj.core.views.render_to_string", return_value=HTML_COM_ANEXO_LOCAL
    ):
        response = CertidaoPublicacaoCrud.DetailView.certidao_publicacao(
            view, requisicao, {}
        )

    assert anexos(response.content) == 0
