import logging

from django.conf import settings
from django.http.response import HttpResponse
from django.template import loader
from django.utils.translation import gettext_lazy as _
from weasyprint import HTML
from weasyprint.urls import URLFetcher

logger = logging.getLogger(__name__)

# Protocolos que o HTML de um PDF pode buscar. Fora deles, como file://, o
# WeasyPrint ignora o recurso: o HTML pode conter texto vindo do usuário.
PDF_PROTOCOLOS_PERMITIDOS = ("http", "https", "data")


def pdf_url_fetcher():
    return URLFetcher(allowed_protocols=PDF_PROTOCOLOS_PERMITIDOS)


def pdf_base_url(request):
    """Base dos endereços relativos do HTML de um PDF.

    Mantém o caminho da página, mas usa o domínio de ``settings.BASE_URL`` em
    vez do ``Host`` da requisição, que o cliente controla.
    """
    return settings.BASE_URL.rstrip("/") + request.get_full_path()


def render_pdf_to_response(request, context, template_name):
    template = loader.get_template(template_name)
    html = template.render(context, request)
    # LOA-LST-082: todo PDF só busca recursos por http, https e data:
    pdf = HTML(
        string=html, base_url=pdf_base_url(request), url_fetcher=pdf_url_fetcher()
    ).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="relatorio_impressos.pdf"'
    response["Content-Transfer-Encoding"] = "binary"

    return response


def make_pdf(
    base_url,
    main_template,
    header_template="",
    footer_template="",
    main_css="",
    header_css="",
):

    # base_url = '.'

    html = HTML(base_url=base_url, string=main_template, url_fetcher=pdf_url_fetcher())

    main_doc = html.render(stylesheets=[])

    def get_page_body(boxes):
        for box in boxes:
            if box.element_tag == "body":
                return box
            return get_page_body(box.all_children())

    if header_template:
        html = HTML(
            base_url=base_url, string=header_template, url_fetcher=pdf_url_fetcher()
        )
        header = html.render(stylesheets=[])

        header_page = header.pages[0]
        header_body = get_page_body(header_page._page_box.all_children())
        header_body = header_body.copy_with_children(header_body.all_children())

    if footer_template:
        html = HTML(
            base_url=base_url, string=footer_template, url_fetcher=pdf_url_fetcher()
        )
        footer = html.render(stylesheets=[])

        footer_page = footer.pages[0]
        footer_body = get_page_body(footer_page._page_box.all_children())
        footer_body = footer_body.copy_with_children(footer_body.all_children())

    for page in main_doc.pages:

        page_body = get_page_body(page._page_box.all_children())

        if header_template:
            page_body.children += header_body.all_children()

        if footer_template:
            page_body.children += footer_body.all_children()

    pdf_file = main_doc.write_pdf()

    return pdf_file
