
from datetime import date
from math import ceil, floor

from braces.views import PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.forms.utils import ErrorList
from django.http.response import HttpResponse
from django.template.defaultfilters import lower
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django_filters.views import FilterView
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle,\
    StyleSheet1
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus.frames import Frame
from reportlab.platypus.para import Paragraph
from sapl.crud.base import make_pagination

from cmj.cerimonial.forms import ImpressoEnderecamentoContatoFilterSet
from cmj.cerimonial.models import Contato
from cmj.core.models import AreaTrabalho


class ImpressoEnderecamentoContatoView(PermissionRequiredMixin, FilterView):
    permission_required = 'cerimonial.print_impressoenderecamento'
    filterset_class = ImpressoEnderecamentoContatoFilterSet
    model = Contato
    template_name = "cerimonial/impressoenderecamento_contato_filter.html"
    container_field = 'workspace__operadores'
    """list_field_names = ['nome', 'data_nascimento']
    """

    paginate_by = 30

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)
        self.object_list = self.filterset.qs

        if 'print' in request.GET and self.object_list.exists():
            if self.filterset.form.cleaned_data['impresso']:
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = \
                    'inline; filename="impresso_enderecamento.pdf"'
                self.build_pdf(response)
                return response
            else:
                self.filterset.form._errors['impresso'] = ErrorList([_(
                    'Selecione o tipo de impresso a ser usado!')])

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _('Não existe Contatos com as '
                                      'condições definidas na busca!'))

        return self.render_to_response(context)

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        try:
            kwargs['workspace'] = AreaTrabalho.objects.filter(
                operadores=self.request.user.pk)[0]
        except:
            raise PermissionDenied(_('Sem permissão de Acesso!'))

        return filterset_class(**kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        kwargs = {}
        if self.container_field:
            kwargs[self.container_field] = self.request.user.pk

        return qs.filter(**kwargs)

    def get_context_data(self, **kwargs):
        count = self.object_list.count()
        context = super(ImpressoEnderecamentoContatoView,
                        self).get_context_data(**kwargs)
        context['count'] = count

        context['title'] = _('Impressão de Etiquetas e Envelopes')
        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        return context

    def build_pdf(self, response):

        cleaned_data = self.filterset.form.cleaned_data

        impresso = cleaned_data['impresso']

        fs = int(impresso.fontsize)
        if cleaned_data['fontsize']:
            fs = int(cleaned_data['fontsize'])

        stylesheet = StyleSheet1()
        stylesheet.add(ParagraphStyle(name='pronome_style',
                                      fontName="Helvetica",
                                      fontSize=fs * 0.8,
                                      leading=fs))
        stylesheet.add(ParagraphStyle(name='nome_style',
                                      fontName="Helvetica-Bold",
                                      fontSize=fs,
                                      leading=fs * 1.3))
        stylesheet.add(ParagraphStyle(name='endereco_style',
                                      fontName="Helvetica",
                                      fontSize=fs * 0.9,
                                      leading=fs))

        pagesize = (float(impresso.largura_pagina) * cm,
                    float(impresso.altura_pagina) * cm)

        ms = pagesize[1] - float(impresso.margem_superior) * cm
        me = float(impresso.margem_esquerda) * cm

        ae = float(impresso.alturaetiqueta) * cm
        le = float(impresso.larguraetiqueta) * cm

        el = float(impresso.entre_linhas) * cm
        ec = float(impresso.entre_colunas) * cm

        col = float(impresso.colunasfolha)
        row = float(impresso.linhasfolha)
        cr = int(col * row)

        p = canvas.Canvas(response, pagesize=pagesize)

        if impresso.rotate:
            p.translate(pagesize[1], 0)
            p.rotate(90)

        i = -1
        for contato in self.object_list.all():
            i += 1
            if i != 0 and i % cr == 0:
                p.showPage()

                if impresso.rotate:
                    p.translate(pagesize[1], 0)
                    p.rotate(90)

            q = floor(i / col) % row
            r = i % int(col)

            l = me + r * ec + r * le
            b = ms - (q + 1) * ae - q * el

            f = Frame(l, b, le, ae,
                      leftPadding=fs / 3,
                      bottomPadding=fs / 3,
                      topPadding=fs / 3,
                      rightPadding=fs / 3,
                      showBoundary=0)
            # f.drawBoundary(p)
            f.addFromList(self.createParagraphs(contato, stylesheet), p)

        p.showPage()
        p.save()

    def createParagraphs(self, contato, stylesheet):

        cleaned_data = self.filterset.form.cleaned_data

        imprimir_cargo = (cleaned_data['imprimir_cargo'] == 'True')\
            if 'imprimir_cargo' in cleaned_data and\
            cleaned_data['imprimir_cargo'] else False

        local_cargo = cleaned_data['local_cargo']\
            if 'local_cargo' in cleaned_data and\
            cleaned_data['local_cargo'] else ''

        story = []

        linha_pronome = ''
        prefixo_nome = ''

        if contato.pronome_tratamento:
            if 'imprimir_pronome' in cleaned_data and\
                    cleaned_data['imprimir_pronome'] == 'True':
                linha_pronome = getattr(
                    contato.pronome_tratamento,
                    'enderecamento_singular_%s' % lower(
                        contato.sexo))
            prefixo_nome = getattr(
                contato.pronome_tratamento,
                'prefixo_nome_singular_%s' % lower(
                    contato.sexo))

        if local_cargo == ImpressoEnderecamentoContatoFilterSet.DEPOIS_PRONOME\
                and imprimir_cargo and (linha_pronome or contato.cargo):
            linha_pronome = '%s - %s' % (linha_pronome, contato.cargo)

        if linha_pronome:
            story.append(Paragraph(
                linha_pronome, stylesheet['pronome_style']))

        linha_nome = '%s %s' % (prefixo_nome, contato.nome)\
            if prefixo_nome else contato.nome

        if local_cargo == ImpressoEnderecamentoContatoFilterSet.LINHA_NOME\
                and imprimir_cargo:

            linha_nome = '%s %s' % (contato.cargo, linha_nome)
            linha_nome = linha_nome.strip()

        linha_nome = linha_nome.upper()\
            if 'nome_maiusculo' in cleaned_data and\
            cleaned_data['nome_maiusculo'] == 'True' else linha_nome

        story.append(Paragraph(linha_nome, stylesheet['nome_style']))

        if local_cargo == ImpressoEnderecamentoContatoFilterSet.DEPOIS_NOME\
                and imprimir_cargo and contato.cargo:
            story.append(
                Paragraph(contato.cargo, stylesheet['endereco_style']))

        endpref = contato.endereco_set.filter(
            preferencial=True).first()
        if endpref:
            endereco = endpref.endereco +\
                (' - ' + endpref.numero if endpref.numero else '') +\
                (' - ' + endpref.complemento if endpref.complemento else '')

            story.append(Paragraph(endereco, stylesheet['endereco_style']))

            b_m_uf = '%s - %s - %s' % (
                endpref.bairro,
                endpref.municipio.nome if endpref.municipio else '',
                endpref.uf)

            story.append(Paragraph(b_m_uf, stylesheet['endereco_style']))
            story.append(Paragraph(endpref.cep, stylesheet['endereco_style']))

        return story

    # obsoleto
    def drawText(self, p, x, y, contato):

        fs = int(self.impresso.fontsize)

        textobject = p.beginText()

        if contato.pronome_tratamento:
            textobject.setTextOrigin(x, y - fs * 0.8)
            textobject.setFont("Helvetica", fs * 0.8)
            textobject.textOut(
                getattr(contato.pronome_tratamento,
                        'enderecamento_singular_%s' % lower(contato.sexo)))
            textobject.moveCursor(0, fs)
        else:
            textobject.setTextOrigin(x, y - fs)

        textobject.setFont("Helvetica-Bold", fs)
        textobject.textOut(contato.nome)

        p.drawText(textobject)
