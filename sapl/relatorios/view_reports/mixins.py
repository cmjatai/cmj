
from django.http import HttpResponse
from cmj.utils_report import make_pdf
from django.template.loader import render_to_string

class RelatorioMixin:
    def get(self, request, *args, **kwargs):
        response = super(RelatorioMixin, self).get(request)

        format = kwargs.get('format', None)

        if 'relatorio' in request.GET:
            format = 'pdf'

        if not format or format != 'pdf':
            return response

        return self.export_pdf(request, response.context_data, *args, **kwargs)

    def export_pdf(self, request, context, *args, **kwargs):
        base_url = request.build_absolute_uri()

        template_pdf = self.get_template_pdf()

        template = render_to_string(template_pdf, context)
        pdf_file = make_pdf(base_url=base_url, main_template=template)

        response = HttpResponse(content_type='application/pdf;')
        response['Content-Disposition'] = 'inline; filename=relatorio.pdf'
        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['Content-Length'] = len(pdf_file)
        response['Content-Type'] = 'application/pdf'
        response['Content-Transfer-Encoding'] = 'binary'
        response.write(pdf_file)
        return response

    def get_template_names(self) -> list[str]:
        prefix = type(self).__name__

        return [f'relatorios/{prefix}_html.html']

    def get_template_pdf(self) -> str:
        prefix = type(self).__name__
        return f'relatorios/pdf/{prefix}_pdf.html'

