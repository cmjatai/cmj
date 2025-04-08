from collections import OrderedDict
import io
import logging

from django.conf import settings
from django.http.response import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from docx import Document
from docx.enum.text import WD_TAB_ALIGNMENT
from docx.shared import Inches, Cm

from cmj.mixins import MultiFormatOutputMixin
from cmj.utils_report import make_pdf
from sapl.base.models import Autor, CasaLegislativa
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Legislatura
from sapl.relatorios.forms import RelatorioMateriasPorAutorFilterSet
from sapl.relatorios.views_old import get_rodape
from sapl.sessao.models import SessaoPlenaria
from django_filters.views import FilterView
from django.utils import formats
from django.contrib import messages
from django.db.models import Count
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.utils import timezone
from sapl.utils import show_results_filter_set
from django.template.loader import render_to_string

class RelatorioMixin:
    def get(self, request, *args, **kwargs):
        response = super(RelatorioMixin, self).get(request)

        if 'relatorio' not in request.GET:
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

        return [f'relatorios/{prefix}_filter.html']

    def get_template_pdf(self) -> str:
        prefix = type(self).__name__
        return f'relatorios/pdf/{prefix}_pdf.html'



class RelatorioMateriasPorAutor(RelatorioMixin, FilterView):
    model = MateriaLegislativa
    filterset_class = RelatorioMateriasPorAutorFilterSet

    data_init = {}

    def get_filterset_kwargs(self, filterset_class):
        super().get_filterset_kwargs(filterset_class)
        self.data_init = kwargs = {'data': self.request.GET or None}

        if kwargs['data'] and 'legislatura_atual' in kwargs['data']:
            kwargs['data'] = {'tipo': '', 'autoria__autor': ''}
            la = Legislatura.cache_legislatura_atual()
            kwargs['data']['data_apresentacao_0'] = formats.date_format(
                la['data_inicio'], "d/m/Y")
            kwargs['data']['data_apresentacao_1'] = formats.date_format(
                la['data_fim'], "d/m/Y")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'title_pdf': _('PortalCMJ - Matérias por Autor'),
        })

        if 'legislatura_atual' not in self.request.GET:
            data = self.request.GET
            context['title'] = _('Matérias por Autor')
        else:
            data = self.data_init['data']
            context['title'] = _('Matérias por Autor - Legislatura Atual')

        context['REQUEST_GET'] = {
            'data_apresentacao_0': data.get('data_apresentacao_0', ''),
            'data_apresentacao_1': data.get('data_apresentacao_1', ''),
            'tipo': data.get('tipo', ''),
            'autoria__autor': data.get('autoria__autor', ''),
        }

        stop_filter = True
        if data:
            for k, v in data.items():
                if v:
                    stop_filter = False

        if data and stop_filter:
            messages.error(
                self.request, 'Informe ao menos um dos filtros abaixo.')
            context['object_list'] = []
            return context

        if not self.filterset.form.is_valid():
            return context
        qtdes = {}
        qs_qtds = context['object_list'].values(
            'tipo__sequencia_regimental', 'tipo__id', 'tipo__descricao', 'tipo__sigla'
        ).annotate(
            total=Count('tipo')
        ).order_by('tipo__sequencia_regimental')
        # for tipo in TipoMateriaLegislativa.objects.all():
        #    qs = context['object_list']
        #    qtde = len(qs.filter(tipo_id=tipo.id))
        #    if qtde > 0:
        #        qtdes[tipo] = qtde
        context['qtdes'] = qs_qtds
        context['qtdes_total'] = context['object_list'].count()

        if context['qtdes_total'] > 10000:
            messages.error(
                self.request,
                'Exitem mais de 10000 registros com o filtro aplicado. '
                'É um processamento muito alto para mostrar todos... '
                'Será mostrado um quadro geral com a totalidade, '
                'mas para uma lista detalhada segmente a pesquisa.')

        qr = self.request.GET.copy(
        ) if 'legislatura_atual' not in self.request.GET else self.data_init['data']

        context['show_results'] = show_results_filter_set(qr)

        if qr['tipo']:
            tipo = int(qr['tipo'])
            context['tipo'] = TipoMateriaLegislativa.objects.get(id=tipo)
        else:
            context['tipo'] = ''
        if qr['autoria__autor']:
            autor = int(qr['autoria__autor'])
            context['autor'] = Autor.objects.get(id=autor)
        else:
            context['autor'] = ''
        if qr['data_apresentacao_0']:
            context['periodo'] = (
                qr['data_apresentacao_0'] +
                ' - ' + qr['data_apresentacao_1'])

        if context['qtdes_total'] > 10000:
            return context

        autor_seleted = context['autor']
        context['result_dict'] = r = {}

        if autor_seleted:
            if autor_seleted not in r:
                r[autor_seleted.nome] = {}
        else:
            context['object_list'] = context['object_list'].annotate(
                autoria_list=ArrayAgg('autoria__autor_id'))

        qs_autores = context['object_list'].values('autoria__autor__id', 'autoria__autor__nome').order_by(
            'autoria__autor__id', 'autoria__autor__nome').distinct()

        autores = {}
        for a in qs_autores:
            if a['autoria__autor__id']:
                autores[a['autoria__autor__id']] = a['autoria__autor__nome']

        contagem = 0
        for m in context['object_list']:
            if autor_seleted:
                if m.ano not in r[autor_seleted.nome]:
                    r[autor_seleted.nome][m.ano] = []
                r[autor_seleted.nome][m.ano].append(m)
            else:
                for a in m.autoria_list:
                    if not a:
                        continue
                    if autores[a] not in r:
                        r[autores[a]] = OrderedDict()
                    if m.ano not in r[autores[a]]:
                        r[autores[a]][m.ano] = []
                    r[autores[a]][m.ano].append(m)
            contagem += 1

            if contagem > 10000:
                break

        context['result_dict'] = {}
        for autor, anos in r.items():
            context['result_dict'][autor] = dict(
                sorted(anos.items(), reverse=True))
        context['result_dict'] = dict(sorted(context['result_dict'].items()))

        return context
