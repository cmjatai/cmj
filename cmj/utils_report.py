from django.utils.translation import gettext_lazy as _
from weasyprint import HTML

def make_pdf(base_url,
             main_template,
             header_template='',
             footer_template='',
             main_css='',
             header_css=''
             ):

    html = HTML(base_url=base_url, string=main_template)

    main_doc = html.render(stylesheets=[])

    def get_page_body(boxes):
        for box in boxes:
            if box.element_tag == 'body':
                return box
            return get_page_body(box.all_children())

    if header_template:
        html = HTML(base_url=base_url, string=header_template)
        header = html.render(
            stylesheets=[])

        header_page = header.pages[0]
        header_body = get_page_body(header_page._page_box.all_children())
        header_body = header_body.copy_with_children(
            header_body.all_children())

    if footer_template:
        html = HTML(base_url=base_url, string=footer_template)
        footer = html.render(
            stylesheets=[])

        footer_page = footer.pages[0]
        footer_body = get_page_body(footer_page._page_box.all_children())
        footer_body = footer_body.copy_with_children(
            footer_body.all_children())

    for page in main_doc.pages:

        page_body = get_page_body(page._page_box.all_children())

        if header_template:
            page_body.children += header_body.all_children()

        if footer_template:
            page_body.children += footer_body.all_children()

    pdf_file = main_doc.write_pdf()
    main_doc

    return pdf_file
