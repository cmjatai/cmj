
from attr import fields
from django.conf import settings
from django.forms import ValidationError
from django.urls.base import reverse
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from haystack.views import SearchView
from django.http import HttpResponseRedirect
import logging
from django.contrib import messages
from django.db.models.query import QuerySet
from cmj.core.models import AreaTrabalho
from cmj.mixins import AudigLogFilterMixin, MultiFormatOutputMixin
from cmj.search.forms import CmjSearchForm, MateriaSearchForm, NormaSearchForm
from cmj.utils import make_pagination
from sapl.base.models import Autor
from sapl.materia.models import MateriaLegislativa
from sapl.materia.views import tipos_autores_materias
from sapl.norma.models import NormaJuridica
from sapl.utils import show_results_filter_set


class CmjSearchView(AudigLogFilterMixin, SearchView):
    results_per_page = 20

    def __call__(self, request):
        self.log(request)
        return SearchView.__call__(self, request)

    def __init__(self, template=None, load_all=True, form_class=None, searchqueryset=None, results_per_page=None):
        super().__init__(
            template=template,
            load_all=load_all,
            form_class=CmjSearchForm,
            searchqueryset=None,
            results_per_page=results_per_page)

    def build_form(self, form_kwargs=None):

        user = self.request.user
        kwargs = {
            'workspaces': None,
            'user': user,
            'load_all': self.load_all,
        }

        if not user.is_anonymous and user.areatrabalho_set.exists():

            at = user.areatrabalho_set.all()
            #.union(
            #   AreaTrabalho.objects.areatrabalho_publica())
            kwargs['workspaces'] = at
        else:
            kwargs['workspaces'] = AreaTrabalho.objects.areatrabalho_publica()

        if form_kwargs:
            kwargs.update(form_kwargs)

        data = self.request.GET or self.request.POST

        if self.searchqueryset is not None:
            kwargs['searchqueryset'] = self.searchqueryset

        return self.form_class(data, **kwargs)

    def get_context(self):
        context = super().get_context()
        #context['title'] = _('Pesquisa Geral')

        data = self.request.GET or self.request.POST

        data = data.copy()
        if 'csrfmiddlewaretoken' in data:
            del data['csrfmiddlewaretoken']

        if 'models' in data:
            models = data.getlist('models')
        else:
            models = []

        context['models'] = ''
        context['is_paginated'] = True

        page_obj = context['page']
        context['page_obj'] = page_obj
        paginator = context['paginator']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        if 'page' in data:
            del data['page']

        context['filter_url'] = (
            '&' + data.urlencode()) if len(data) > 0 else ''

        for m in models:
            context['models'] = context['models'] + '&models=' + m
        return context


class MateriaSearchView(AudigLogFilterMixin, MultiFormatOutputMixin, SearchView, ):
    results_per_page = 20
    template = 'search/materialegislativa_search.html'

    formats_export = 'csv', 'xlsx', 'json', 'pdf'

    model = MateriaLegislativa
    fields_base_report = [
        'id',
        'ano',
        'numero',
        'tipo__sigla',
        'tipo__descricao',
        'autoria__autor__nome',
        'texto_original',
        'ementa'
    ]

    queryset_values_for_formats = {
        'csv': True,
        'xlsx': True,
        'json': True,
        'pdf': False,
    }

    fields_pdf_report = [
        'epigrafe_ementa',
        'autores_for_pdf',
    ]

    fields_report = {
        'csv': fields_base_report,
        'xlsx': fields_base_report,
        'json': fields_base_report,
        'pdf': fields_pdf_report,
    }

    def hook_epigrafe_ementa(self, obj):
        html = f'''
                <a href="{self.hook_texto_original(obj)}">{obj.epigrafe}</a><br>
                {obj.ementa}
        '''
        return html

    def hook_header_autores_for_pdf(self):
        return force_str(_('Autores'))

    def hook_autores_for_pdf(self, obj):
        autores = list(obj.autores.values_list('nome', flat=True))
        autores = list(map(lambda x: f'<span class="whitespace">{x}</span>', autores))
        return autores


    def hook_header_epigrafe_ementa(self):
        return force_str(_('Epígrafe / Ementa'))

    def hook_header_texto_original(self):
        return force_str(_('Link para Matéria Legislativa'))

    def hook_texto_original(self, obj):
        id = obj["id"] if isinstance(obj, dict) else obj.id
        return f'{settings.SITE_URL}/materia/{id}'

    def __call__(self, request):
        self.log(request)
        return SearchView.__call__(self, request)

    def __init__(self, template=None, load_all=True, form_class=None, searchqueryset=None, results_per_page=None):
        super().__init__(
            template=template,
            load_all=load_all,
            form_class=MateriaSearchForm,
            searchqueryset=None,
            results_per_page=results_per_page)

    def build_form(self, form_kwargs=None):

        kwargs = {
            'load_all': self.load_all,
        }

        if form_kwargs:
            kwargs.update(form_kwargs)

        data = self.request.GET or self.request.POST

        if self.searchqueryset is not None:
            kwargs['searchqueryset'] = self.searchqueryset

        return self.form_class(data, **kwargs)

    def view_actions(self):
        u = self.request.user
        return {
            'search_url': '?',
            'verbose_name': _('Materia Legislativa'),
            'create_url': '' if u.is_anonymous or
            not u.has_perm('materia.add_materialegislativa') else
            reverse('sapl.materia:materialegislativa_create'),
            'tipos_autores_materias': self.tipo_autores_materias,
        }

    def get_context(self):
        context = super().get_context()
        #context['title'] = _('Pesquisa Geral')

        data = self.request.GET or self.request.POST

        data = data.copy()
        if 'csrfmiddlewaretoken' in data:
            del data['csrfmiddlewaretoken']

        context['tipo_listagem'] = self.form.cleaned_data.get(
            'tipo_listagem', None)
        context['is_paginated'] = True

        page_obj = context['page']
        context['page_obj'] = page_obj
        paginator = context['paginator']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        if 'page' in data:
            del data['page']

        context['view'] = self.view_actions()

        qr = self.request.GET.copy()
        context['show_results'] = show_results_filter_set(qr)
        if not context['show_results']:
            del context['view']['search_url']
            #context['tipos_autores_materias'] = self.tipo_autores_materias()

        context['filter_url'] = (
            '&' + data.urlencode()) if len(data) > 0 else ''

        return context

    def tipo_autores_materias(self):
        acesso_rapido_list = list(tipos_autores_materias(
            None, restricao_regimental=False).items()
        )

        acesso_rapido_list.sort(
            key=lambda tup: tup[0].sequencia_regimental)

        return acesso_rapido_list

    def render_to_pdf(self, context):

        format_result = getattr(self.request, self.request.method).get('format', None)
        if format_result == 'pdf':
            cd = self.form.cleaned_data if self.form.is_valid() else {}

            filters = []

            for k, v in cd.items():

                if not v:
                    continue

                if k in ('ordenacao', 'tipo_listagem'):
                    continue

                label = self.form.fields[k].label if k in self.form.fields else k

                if k == 'autoria_is':
                    filtro = f'<strong>{label}:</strong> {Autor.objects.get(id=v).nome}'
                elif isinstance(v, (list, tuple)):
                    filtro = f'<strong>{label}:</strong> {", ".join([str(x) for x in v])}'
                elif not isinstance(v, QuerySet):
                    filtro = f'<strong>{label}:</strong> {v}'
                else:
                    items = self.form.fields[k].queryset.filter(id__in=v).values_list('descricao', flat=True)
                    filtro = f'<strong>{label}:</strong> {", ".join([str(x) for x in items])}'
                filters.append(filtro)

            if filters:
                filters.insert(0, '<strong>FILTROS APLICADOS</strong>')
                filters.append('')

            context['filters'] = '<br>'.join(filters)

        return super().render_to_pdf(context)

    def to_json(self, context, for_format='json'):
        if context['object_list'].count() > 5000:
            raise ValidationError(_(
                'O número máximo de resultados para exportação em PDF é de 5000 registros. '
                'Por favor, refine sua pesquisa.'
            ))
        return super().to_json(context, for_format)

    def create_response(self):

        try:
            return super().create_response()
        except ValidationError as e:
            messages.error(self.request, e.message)
            return HttpResponseRedirect(
                reverse('cmj.search:materia_haystack_search')
            )


class NormaSearchView(AudigLogFilterMixin,  MultiFormatOutputMixin, SearchView, ):
    results_per_page = 50
    template = 'search/normajuridica_search.html'

    model = NormaJuridica
    fields_base_report = [
        'id', 'ano', 'numero', 'tipo__sigla', 'tipo__descricao', 'texto_integral', 'ementa'
    ]
    fields_report = {
        'csv': fields_base_report,
        'xlsx': fields_base_report,
        'json': fields_base_report,
    }

    def hook_header_texto_integral(self):
        return force_str(_('Link para Norma'))

    def hook_texto_integral(self, obj):
        id = obj["id"] if isinstance(obj, dict) else obj.id
        return f'{settings.SITE_URL}/norma/{id}'

    def __call__(self, request):
        self.log(request)
        return SearchView.__call__(self, request)

    def __init__(self, template=None, load_all=True, form_class=None, searchqueryset=None, results_per_page=None):
        super().__init__(
            template=template,
            load_all=load_all,
            form_class=NormaSearchForm,
            searchqueryset=None,
            results_per_page=results_per_page)

    def build_form(self, form_kwargs=None):

        kwargs = {
            'load_all': self.load_all,
        }

        if form_kwargs:
            kwargs.update(form_kwargs)

        data = self.request.GET or self.request.POST

        if self.searchqueryset is not None:
            kwargs['searchqueryset'] = self.searchqueryset

        return self.form_class(data, **kwargs)

    def urls(self):
        u = self.request.user
        return {
            'search_url': '?',
            'verbose_name': _('Norma Jurídica'),
            'create_url': '' if u.is_anonymous or
            not u.has_perm('norma.add_normajuridica') else
            reverse('sapl.norma:normajuridica_create')
        }

    def get_context(self):
        context = super().get_context()

        data = self.request.GET or self.request.POST

        data = data.copy()
        if 'csrfmiddlewaretoken' in data:
            del data['csrfmiddlewaretoken']

        context['is_paginated'] = True

        page_obj = context['page']
        context['page_obj'] = page_obj
        paginator = context['paginator']
        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        if 'page' in data:
            del data['page']

        context['view'] = self.urls()

        object_list = context['page'].object_list
        NormaJuridica.objects.filter(
            id__in=[obj.pk for obj in object_list]
        ).select_related('tipo')

        qr = self.request.GET.copy()
        context['show_results'] = show_results_filter_set(qr)
        if not context['show_results']:
            del context['view']['search_url']

        context['filter_url'] = (
            '&' + data.urlencode()) if len(data) > 0 else ''

        return context
