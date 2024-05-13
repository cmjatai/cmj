
from django.conf import settings
from django.urls.base import reverse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from haystack.views import SearchView

from cmj.core.models import AreaTrabalho
from cmj.mixins import AudigLogFilterMixin, MultiFormatOutputMixin
from cmj.search.forms import CmjSearchForm, MateriaSearchForm, NormaSearchForm
from cmj.utils import make_pagination
from sapl.materia.models import MateriaLegislativa
from sapl.materia.views import tipos_autores_materias
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

    model = MateriaLegislativa
    queryset_values_for_formats = False
    fields_base_report = [
        'object__id',
        'object__ano',
        'object__numero',
        'object__tipo__sigla',
        'object__tipo__descricao',
        'object__autores',
        'object__texto_original',
        'object__ementa'
    ]
    fields_report = {
        'csv': fields_base_report,
        'xlsx': fields_base_report,
        'json': fields_base_report,
    }

    def hook_header_object__texto_original(self):
        return force_text(_('Link para Matéria Legislativa'))

    def hook_object__texto_original(self, obj):
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

    def urls(self):
        u = self.request.user
        return {
            'search_url': '?',
            'verbose_name': _('Materia Legislativa'),
            'create_url': '' if u.is_anonymous or
            not u.has_perm('materia.add_materialegislativa') else
            reverse('sapl.materia:materialegislativa_create')
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

        context['view'] = self.urls()

        qr = self.request.GET.copy()
        context['show_results'] = show_results_filter_set(qr)
        if not context['show_results']:
            del context['view']['search_url']

            acesso_rapido_list = list(tipos_autores_materias(
                None, restricao_regimental=False).items()
            )

            acesso_rapido_list.sort(
                key=lambda tup: tup[0].sequencia_regimental)

            context['tipos_autores_materias'] = acesso_rapido_list

        context['filter_url'] = (
            '&' + data.urlencode()) if len(data) > 0 else ''

        return context


class NormaSearchView(AudigLogFilterMixin, SearchView, ):
    results_per_page = 50
    template = 'search/normajuridica_search.html'

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

        qr = self.request.GET.copy()
        context['show_results'] = show_results_filter_set(qr)
        if not context['show_results']:
            del context['view']['search_url']

        context['filter_url'] = (
            '&' + data.urlencode()) if len(data) > 0 else ''

        return context
