
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import ugettext_lazy as _
from django_filters.views import FilterView
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet, EmptySearchQuerySet
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication,\
    BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from sapl.crud.base import Crud, make_pagination
from whoosh.lang import snowball

from cmj.core.forms import TrechoFilterSet, LogradouroSearchForm
from cmj.core.models import Cep, TipoLogradouro, Logradouro, RegiaoMunicipal,\
    Distrito, Bairro, Trecho
from cmj.core.rules import rules_patterns
from cmj.core.serializers import TrechoSearchSerializer, TrechoSerializer
from cmj.globalrules import globalrules


globalrules.rules.config_groups(rules_patterns)

CepCrud = Crud.build(Cep, 'cep')
RegiaoMunicipalCrud = Crud.build(RegiaoMunicipal, 'regiao_municipal')
DistritoCrud = Crud.build(Distrito, 'distrito')
BairroCrud = Crud.build(Bairro, 'bairro')
TipoLogradouroCrud = Crud.build(TipoLogradouro, 'tipo_logradouro')
LogradouroCrud = Crud.build(Logradouro, 'logradouro')
TrechoCrud = Crud.build(Trecho, 'trecho')


# dict e primeiro def abaixo não estão sendo usados mas são um lembrete
# para uso se stemmers
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

# view usando django-filter... não está sendo usado


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


class TrechoSearchView(PermissionRequiredMixin, SearchView):
    template_name = 'search/search.html'
    queryset = SearchQuerySet()
    form_class = LogradouroSearchForm
    permission_required = 'core.search_trecho'

    paginate_by = 20

    def get(self, request, *args, **kwargs):
        return SearchView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TrechoSearchView,
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


class TrechoJsonSearchView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TrechoSearchSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    page_size = 0

    def get_queryset(self, *args, **kwargs):
        request = self.request
        queryset = EmptySearchQuerySet()

        if request.GET.get('q') is not None:
            query = request.GET.get('q')
            queryset = SearchQuerySet().auto_query(query, 'text')

        return queryset


class TrechoJsonView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TrechoSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    queryset = Trecho.objects.all()
