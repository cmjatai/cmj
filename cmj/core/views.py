
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import ugettext_lazy as _
from django_filters.views import FilterView
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet
from sapl.crud.base import Crud, make_pagination
from whoosh.lang import snowball

from cmj.core.forms import TrechoFilterSet, LogradouroSearchForm
from cmj.core.models import Cep, TipoLogradouro, Logradouro, RegiaoMunicipal,\
    Distrito, Bairro, Trecho


CepCrud = Crud.build(Cep, 'cep')
RegiaoMunicipalCrud = Crud.build(RegiaoMunicipal, 'regiao_municipal')
DistritoCrud = Crud.build(Distrito, 'distrito')
BairroCrud = Crud.build(Bairro, 'bairro')
TipoLogradouroCrud = Crud.build(TipoLogradouro, 'tipo_logradouro')
LogradouroCrud = Crud.build(Logradouro, 'logradouro')
TrechoCrud = Crud.build(Trecho, 'trecho')


STEMMERS = {
    'pt-BR': snowball.portugese.PortugueseStemmer()
}


def stem(text, lang):
    stemmer = STEMMERS.get(lang)

    if not stemmer:
        return ''

    text_stemmed = []
    for term in text.split(' '):
        term = stemmer.stem(term)
        text_stemmed.append(term)
    text_stemmed = ' '.join(text_stemmed)

    return text_stemmed


class EnderecoPesquisaView(FilterView):
    filterset_class = TrechoFilterSet

    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super(EnderecoPesquisaView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Pesquisa de Endereços')
        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        return context


class LogradouroSearchView(PermissionRequiredMixin, SearchView):
    template_name = 'search/search.html'
    queryset = SearchQuerySet()
    form_class = LogradouroSearchForm
    permission_required = 'core.search_trecho'

    paginate_by = 20

    def get(self, request, *args, **kwargs):
        return SearchView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LogradouroSearchView,
                        self).get_context_data(**kwargs)
        context['title'] = _('Pesquisa de Endereços')
        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        return context

    def get_queryset(self):

        return SearchView.get_queryset(self)
