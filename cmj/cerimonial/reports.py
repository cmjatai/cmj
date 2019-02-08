
from _io import BytesIO
from datetime import date, datetime
from math import ceil, floor

from braces.views import PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms.utils import ErrorList
from django.http.response import HttpResponse
from django.template.defaultfilters import lower
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django_filters.views import FilterView
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle,\
    StyleSheet1, _baseFontNameB
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.para import Paragraph
from reportlab.platypus.tables import Table, TableStyle, LongTable

from cmj.cerimonial.forms import ImpressoEnderecamentoContatoFilterSet,\
    ContatoAgrupadoPorProcessoFilterSet, ContatoAgrupadoPorGrupoFilterSet
from cmj.cerimonial.models import Contato, Processo
from cmj.core.models import AreaTrabalho
from cmj.crud.base import make_pagination


class ImpressoEnderecamentoContatoView(PermissionRequiredMixin, FilterView):
    permission_required = 'cerimonial.print_impressoenderecamento'
    filterset_class = ImpressoEnderecamentoContatoFilterSet
    model = Contato
    template_name = "cerimonial/filter_impressoenderecamento_contato.html"
    container_field = 'workspace__operadores'
    """list_field_names = ['nome', 'data_nascimento']
    """

    paginate_by = 30

    @property
    def is_contained(self):
        return True

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
                endpref.bairro if endpref.bairro else '',
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


class RelatorioContatoAgrupadoPorGrupoView(
        PermissionRequiredMixin, FilterView):
    permission_required = 'cerimonial.print_rel_contato_agrupado_por_grupo'
    filterset_class = ContatoAgrupadoPorGrupoFilterSet
    model = Contato
    template_name = "cerimonial/filter_contato_agrupado_por_grupo.html"
    container_field = 'workspace__operadores'

    paginate_by = 30

    @property
    def is_contained(self):
        return True

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
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = \
                'inline; filename="relatorio.pdf"'
            self.build_pdf(response)
            return response

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _('Não existe Contato com as '
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
        context = super(RelatorioContatoAgrupadoPorGrupoView,
                        self).get_context_data(**kwargs)
        context['count'] = count

        context['title'] = _(
            'Relatório de Contatos Com Agrupamento Por Grupos')
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


class RelatorioContatoAgrupadoPorProcessoView(
        PermissionRequiredMixin, FilterView):
    permission_required = 'cerimonial.print_rel_contato_agrupado_por_processo'
    filterset_class = ContatoAgrupadoPorProcessoFilterSet
    model = Processo
    template_name = "cerimonial/filter_contato_agrupado_por_processo.html"
    container_field = 'workspace__operadores'

    paginate_by = 30

    @property
    def is_contained(self):
        return True

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
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = \
                'inline; filename="relatorio.pdf"'
            self.build_pdf(response)
            return response

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)

        if len(request.GET) and not len(self.filterset.form.errors)\
                and not self.object_list.exists():
            messages.error(request, _('Não existe Processo com as '
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
        context = super(RelatorioContatoAgrupadoPorProcessoView,
                        self).get_context_data(**kwargs)
        context['count'] = count

        context['title'] = _(
            'Relatório de Contatos Com Agrupamento Por Processos')
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

        agrupamento = cleaned_data['agrupamento']

        elements = []

        #print('data ini', datetime.now())
        data = self.get_data()
        #print('data fim', datetime.now())

        style = TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LEADING', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.1, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ])
        style.add('VALIGN', (0, 0), (-1, -1), 'MIDDLE')

        #print('enumerate ini', datetime.now())
        for i, value in enumerate(data):
            if len(value) <= 1:
                style.add('SPAN', (0, i), (-1, i))

            if len(value) == 0:
                style.add('INNERGRID', (0, i), (-1, i), 0, colors.black),
                style.add('GRID', (0, i), (-1, i), -1, colors.white)
                style.add('LINEABOVE', (0, i), (-1, i), 0.1, colors.black)

            if len(value) == 1:
                style.add('LINEABOVE', (0, i), (-1, i), 0.1, colors.black)

        #print('enumerate fim', datetime.now())
        # if not agrupamento or agrupamento == 'sem_agrupamento':
        #    style.add('ALIGN', (0, 0), (0, -1), 'CENTER')

        #print('table ini', datetime.now())
        rowHeights = 20
        t = LongTable(data, rowHeights=rowHeights, splitByRow=True)
        t.setStyle(style)
        if len(t._argW) == 5:
            t._argW[0] = 1.8 * cm
            t._argW[1] = 6 * cm
            t._argW[2] = 6.5 * cm
            t._argW[3] = 9.5 * cm
            t._argW[4] = 2.4 * cm
        elif len(t._argW) == 4:
            t._argW[0] = 2 * cm
            t._argW[1] = 10 * cm
            t._argW[2] = 11.5 * cm
            t._argW[3] = 3 * cm

        for i, value in enumerate(data):
            if len(value) == 0:
                t._argH[i] = 7
                continue
            for cell in value:
                if isinstance(cell, list):
                    t._argH[i] = (rowHeights) * (
                        len(cell) - (0 if len(cell) > 1 else 0))
                    break

        elements.append(t)
        #print('table fim', datetime.now())

        #print('build ini', datetime.now())
        doc = SimpleDocTemplate(
            response,
            pagesize=landscape(A4),
            rightMargin=1.25 * cm,
            leftMargin=1.25 * cm,
            topMargin=1.1 * cm,
            bottomMargin=0.8 * cm)
        doc.build(elements)
        #print('build fim', datetime.now())

    def get_data(self):
        """data ini 2016-08-29 09:45:43.018039
        data fim 2016-08-29 09:47:16.667659
        enumerate ini 2016-08-29 09:47:16.667745
        enumerate fim 2016-08-29 09:47:16.671923
        table ini 2016-08-29 09:47:16.671954
        table fim 2016-08-29 09:47:17.233298
        doc ini 2016-08-29 09:47:17.233338
        doc fim 2016-08-29 10:13:36.675347"""
        # 211 páginas
        # 6723

        MAX_TITULO = 80

        s = getSampleStyleSheet()
        h3 = s["Heading3"]
        h3.fontName = _baseFontNameB
        h3.alignment = TA_CENTER

        h4 = s["Heading4"]
        h4.fontName = _baseFontNameB

        h5 = s["Heading5"]
        h5.fontName = _baseFontNameB
        h5.alignment = TA_CENTER

        s = s["BodyText"]
        s.wordWrap = None  # 'LTR'
        s.spaceBefore = 0
        s.fontSize = 8
        s.leading = 8

        s_min = getSampleStyleSheet()
        s_min = s_min["BodyText"]
        s_min.wordWrap = None  # 'LTR'
        s_min.spaceBefore = 0
        s_min.fontSize = 6
        s_min.leading = 8

        s_center = getSampleStyleSheet()
        s_center = s_center["BodyText"]
        s_center.wordWrap = None  # 'LTR'
        s_center.spaceBefore = 0
        s_center.alignment = TA_CENTER
        s_center.fontSize = 8
        s_center.leading = 8

        s_right = getSampleStyleSheet()
        s_right = s_right["BodyText"]
        s_right.wordWrap = None  # 'LTR'
        s_right.spaceBefore = 0
        s_right.alignment = TA_RIGHT
        s_right.fontSize = 8
        s_right.leading = 8

        cleaned_data = self.filterset.form.cleaned_data

        agrupamento = cleaned_data['agrupamento']

        agrupamento = '' if agrupamento == 'sem_agrupamento' else agrupamento

        if not agrupamento:
            self.object_list = self.object_list.order_by(
                'data', 'titulo', 'contatos__nome')
        else:
            self.object_list = self.object_list.order_by(
                agrupamento).distinct(agrupamento).values_list(
                agrupamento, flat=True)

        data = []
        cabec = []
        cabec.append(Paragraph(_('Data'), h5))
        if agrupamento != 'titulo':
            cabec.append(Paragraph(_('Título'), h5))
        cabec.append(Paragraph(_('Nome'), h5))
        cabec.append(Paragraph(_('Endereço'), h5))
        cabec.append(Paragraph(_('Telefone'), h5))

        where = self.object_list.query.where

        for p in self.object_list.all():

            contatos_query = []
            item = []

            label_agrupamento = ''
            if not p or isinstance(p, str):
                label_agrupamento = dict(
                    ContatoAgrupadoPorProcessoFilterSet.AGRUPAMENTO_CHOICE)
                label_agrupamento = force_text(
                    label_agrupamento[agrupamento])

            if not data:
                tit_relatorio = _('Relatório de Contatos e Processos')
                tit_relatorio = force_text(tit_relatorio) + ' ' + ((
                    force_text(_('Agrupados')) + ' ' +
                    label_agrupamento) if label_agrupamento else (
                    force_text(_('Sem Agrupamento')) +
                    ' ' + label_agrupamento))

                data.append([Paragraph(tit_relatorio, h3)])

                if not label_agrupamento:
                    data.append(cabec)

            if not p or isinstance(p, str):
                data.append([])

                data.append([Paragraph((
                    label_agrupamento + ' - ' + str(p)) if p
                    else (force_text(_('Sem Agrupamento')) +
                          ' ' + label_agrupamento), h4)])

                data.append(cabec)

                p_filter = (('processo_set__' + agrupamento, p),)
                if not p:
                    p_filter = (
                        (p_filter[0][0] + '__isnull', True),
                        (p_filter[0][0] + '__exact', '')
                    )

                q = Q()
                for filtro in p_filter:
                    filtro_dict = {filtro[0]: filtro[1]}
                    q = q | Q(**filtro_dict)

                contatos_query = Contato.objects.all()
                contatos_query.query.where = where.clone()
                contatos_query = contatos_query.filter(q)

                params = {self.container_field: self.request.user.pk}
                contatos_query = contatos_query.filter(**params)

                contatos_query = contatos_query.order_by(
                    'processo_set__' + agrupamento,
                    'processo_set__data',
                    'nome',
                    'endereco_set__bairro__nome',
                    'endereco_set__endereco').distinct(
                    'processo_set__' + agrupamento,
                    'processo_set__data',
                    'nome')

            else:
                item = [
                    Paragraph(p.data.strftime('%d/%m/%Y'), s_center),
                    Paragraph(
                        str(p.titulo) if len(p.titulo) < MAX_TITULO
                        else p.titulo[:MAX_TITULO] +
                        force_text(_(' (Continua...)')), s if len(p.titulo) < MAX_TITULO else s_min)]

                contatos_query = p.contatos.all()

            contatos = []
            enderecos = []
            telefones = []
            for contato in contatos_query:

                if agrupamento:
                    contatos = []
                    enderecos = []
                    telefones = []
                    item = []

                if contatos:
                    contatos.append(Paragraph('--------------', s_center))
                    enderecos.append(Paragraph('--------------', s_center))
                    telefones.append(Paragraph('--------------', s_center))

                contatos.append(Paragraph(str(contato.nome), s))

                endpref = contato.endereco_set.filter(
                    preferencial=True).first()
                endereco = ''
                if endpref:
                    endereco = endpref.endereco +\
                        (' - ' + endpref.numero
                         if endpref.numero else '') +\
                        (' - ' + endpref.complemento
                         if endpref.complemento else '')

                    endereco = '%s - %s - %s - %s' % (
                        endereco,
                        endpref.bairro if endpref.bairro else '',
                        endpref.municipio.nome
                        if endpref.municipio else '',
                        endpref.uf)

                enderecos.append(Paragraph(endereco, s))

                tels = '\n'.join(map(
                    lambda x: str(x), list(contato.telefone_set.all())
                )) if contato.telefone_set.exists() else ''

                telefones.append((Paragraph(tels, s_center)))

                if agrupamento:
                    params = {'contatos': contato,
                              self.container_field: self.request.user.pk}
                    processos = Processo.objects.all()
                    processos.query.where = where.clone()
                    processos = processos.filter(**params)

                    ps = None
                    data_abertura = []
                    titulo = []
                    for ps in processos:

                        if data_abertura:
                            data_abertura.append(
                                Paragraph('--------------', s_center))
                            if agrupamento != 'titulo':
                                titulo.append(
                                    Paragraph('--------------', s_center))

                        data_abertura.append(
                            Paragraph(
                                ps.data.strftime('%d/%m/%Y'), s_center))

                        if agrupamento != 'titulo':
                            titulo.append(
                                Paragraph(
                                    str(ps.titulo)
                                    if len(ps.titulo) < MAX_TITULO
                                    else ps.titulo[:MAX_TITULO] +
                                    force_text(_(' (Continua...)')),
                                    s if len(ps.titulo) < MAX_TITULO
                                    else s_min))
                    if not ps:
                        data_abertura.append(Paragraph('-----', s_center))
                        if agrupamento != 'titulo':
                            titulo.append(Paragraph('-----', s_center))

                    if len(data_abertura) == 1:
                        item += data_abertura
                        if agrupamento != 'titulo':
                            item += titulo
                    else:
                        item.append(data_abertura)
                        if agrupamento != 'titulo':
                            item.append(titulo)

                    item.append(contatos[0])
                    item.append(enderecos[0])
                    item.append(telefones[0])

                    data.append(item)

                    """if len(data) > 2000:
                        return data"""

            if not agrupamento:
                if len(contatos) == 0:
                    item.append('-----')
                else:
                    item.append(contatos)
                    item.append(enderecos)
                    item.append(telefones)

                data.append(item)

                """if len(data) > 2000:
                    return data"""

        return data
