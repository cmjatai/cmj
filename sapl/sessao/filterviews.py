
import logging
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from crispy_forms.layout import (
    HTML, Button, Field, Fieldset, Layout, Row, Div
    )
from django.contrib import messages
from cmj.mixins import AudigLogFilterMixin, MultiFormatOutputMixin
from sapl.crispy_layout_mixin import SaplFormHelper, SaplFormLayout, to_row
from sapl.crud.base import make_pagination
from sapl.sessao.forms import SessaoPlenariaFilterSet
from sapl.sessao.models import RegistroVotacao, SessaoPlenaria
from sapl.utils import choice_anos_com_votacao, show_results_filter_set
from django_filters.views import FilterView
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django_filters import FilterSet, ChoiceFilter

logger = logging.getLogger(__name__)

class RegistroVotacaoFilterSet(FilterSet):

    ano = ChoiceFilter(
        required=False,
        label='Ano da Votação',
        field_name='data_hora__year',
        choices=choice_anos_com_votacao
    )

    class Meta:
        model = RegistroVotacao
        fields = {
            'tipo_resultado_votacao': ['exact'],
            'ordem__tipo_votacao': ['exact'],
            'materia__tipo': ['exact'],
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        row1 = to_row(
            [
                ('ano', 2),
                ('ordem__tipo_votacao', 3),
                ('tipo_resultado_votacao', 3),
                ('materia__tipo', 4),
            ]
        )

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = SaplFormLayout(
            Fieldset(_('Pesquisa Parametrizada'),
                     row1, ),
            save_label=_('Pesquisar'),
            cancel_label=None
        )


class RegistroVotacaoFilterView(AudigLogFilterMixin, MultiFormatOutputMixin, FilterView):
    model = RegistroVotacao
    filterset_class = RegistroVotacaoFilterSet
    paginate_by = 30
    ordering = (
        '-data_hora__year',
        '-data_hora__month',
        '-data_hora__day',
        '-ordem__sessao_plenaria',
        '-ordem__numero_ordem')

    formats_impl = 'csv', 'xlsx', 'json', 'pdf'

    fields_base_report = [
        'id',
        'materia',
        'numero_votos_sim',
        'numero_votos_nao',
        'numero_abstencoes',
        'tipo_resultado_votacao',
    ]
    fields_report = {
        'csv': fields_base_report,
        'xlsx': fields_base_report,
        'json': fields_base_report,
    }

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except ValidationError as e:
            messages.error(request, e.message)
            logger.warning(f"Erro de validação: {e}")
            return HttpResponseRedirect(
                reverse('sapl.sessao:votacoes_pesquisa')
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        format_result = getattr(self.request, self.request.method).get('format', None)

        context['title'] = _('Registros de Votação')

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        #context['bg_title'] = 'bg-yellow text-white'

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        cd = self.filterset.form.cleaned_data if self.filterset.form.is_valid() else {}

        if format_result == 'pdf' and not cd.get('ano', ''):
            raise ValidationError(_(
                'Para gerar o relatório em PDF, é necessário filtrar ao menos por ano da votação.'
            ))

        filters = []
        if cd.get('ano', ''):
            filtro = f'<strong>Ano de Votação:</strong> {cd["ano"]}'
            filters.append(filtro)

        if cd.get('ordem__tipo_votacao', ''):
            filtro = f'<strong>Tipo de Votação:</strong> {cd["ordem__tipo_votacao"]}'
            filters.append(filtro)
        if cd.get('tipo_resultado_votacao', ''):
            filtro = f'<strong>Resultado da Votação:</strong> {cd["tipo_resultado_votacao"]}'
            filters.append(filtro)
        if cd.get('materia__tipo', ''):
            filtro = f'<strong>Tipo de Matéria:</strong> {cd["materia__tipo"]}'
            filters.append(filtro)

        if filters:
            filters.insert(0, '<strong>FILTROS APLICADOS</strong>')
            filters.append('')

        context['filters'] = '<br>'.join(filters)
        context['title_pdf'] = _('Relatório de Registros de Votação')

        return context


class PesquisarSessaoPlenariaView(AudigLogFilterMixin, MultiFormatOutputMixin, FilterView):
    model = SessaoPlenaria
    filterset_class = SessaoPlenariaFilterSet
    paginate_by = 20

    viewname = 'sapl.sessao:pesquisar_sessao'

    queryset_values_for_formats = False

    fields_base_report = [
        'id',
        'data_inicio',
        'hora_inicio',
        'data_fim',
        'hora_fim',
        '',
    ]
    fields_report = {
        'csv': fields_base_report,
        'xlsx': fields_base_report,
        'json': fields_base_report,
    }
    def hook_header_(self):
        return force_str(_('Título'))

    def hook_(self, obj):
        return str(obj)

    def hook_data_inicio(self, obj):
        return str(obj.data_inicio or '')

    def hook_data_fim(self, obj):
        return str(obj.data_fim or '')

    def get_queryset(self):
        qs = FilterView.get_queryset(self)
        qs = qs.select_related(
            'tipo', 'sessao_legislativa', 'legislatura').distinct().order_by(
            '-legislatura__numero', '-data_inicio', '-hora_inicio')
        return qs

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Pesquisar Sessão Plenária')

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        context['bg_title'] = 'bg-yellow text-white'

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        data = self.filterset.data
        if data and data.get('data_inicio__year') is not None:
            url = "&" + str(self.request.META['QUERY_STRING'])
            if url.startswith("&page"):
                ponto_comeco = url.find('data_inicio__year=') - 1
                url = url[ponto_comeco:]
            context['filter_url'] = url

        context['numero_res'] = len(self.object_list)

        return context

    def get(self, request, *args, **kwargs):

        r = super().get(request)

        data = self.filterset.data
        if not data:
            return HttpResponseRedirect(
                reverse(
                    self.viewname
                ) + f'?pesquisar='
            )

        return r

