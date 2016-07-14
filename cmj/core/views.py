
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.urlresolvers import reverse
from django.forms.utils import ErrorList
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django_filters.views import FilterView
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet, EmptySearchQuerySet
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication,\
    BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from sapl.crud.base import Crud, make_pagination
from sapl.parlamentares.models import Partido, Filiacao
from whoosh.lang import snowball

from cmj.core.forms import TrechoFilterSet, LogradouroSearchForm,\
    OperadorAreaTrabalhoForm, ImpressoEnderecamentoForm
from cmj.core.models import Cep, TipoLogradouro, Logradouro, RegiaoMunicipal,\
    Distrito, Bairro, Trecho, AreaTrabalho, OperadorAreaTrabalho,\
    ImpressoEnderecamento
from cmj.core.rules import rules_patterns
from cmj.core.serializers import TrechoSearchSerializer, TrechoSerializer
from cmj.globalrules import globalrules
from cmj.globalrules.crud_custom import DetailMasterCrud,\
    MasterDetailCrudPermission


globalrules.rules.config_groups(rules_patterns)

CepCrud = DetailMasterCrud.build(Cep, None, 'cep')
RegiaoMunicipalCrud = DetailMasterCrud.build(
    RegiaoMunicipal, None,  'regiao_municipal')
DistritoCrud = DetailMasterCrud.build(Distrito, None, 'distrito')
BairroCrud = DetailMasterCrud.build(Bairro, None, 'bairro')
TipoLogradouroCrud = DetailMasterCrud.build(
    TipoLogradouro, None, 'tipo_logradouro')
LogradouroCrud = DetailMasterCrud.build(Logradouro, None, 'logradouro')
TrechoCrud = DetailMasterCrud.build(Trecho, None, 'trecho')


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


class AreaTrabalhoCrud(DetailMasterCrud):
    model = AreaTrabalho
    model_set = 'operadorareatrabalho_set'

    class BaseMixin(DetailMasterCrud.BaseMixin):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = 'core/subnav_areatrabalho.yaml'
            return context

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_set = ['user_name', ]


class OperadorAreaTrabalhoCrud(MasterDetailCrudPermission):
    parent_field = 'areatrabalho'
    model = OperadorAreaTrabalho
    help_path = 'operadorareatrabalho'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context[
                'subnav_template_name'] = 'core/subnav_areatrabalho.yaml'
            return context

    class UpdateView(MasterDetailCrudPermission.UpdateView):
        form_class = OperadorAreaTrabalhoForm

        # TODO tornar operador readonly na edição
        def form_valid(self, form):
            old = OperadorAreaTrabalho.objects.get(pk=self.object.pk)

            groups = list(old.grupos_associados.values_list('name', flat=True))
            globalrules.rules.groups_remove_user(old.user, groups)

            response = super().form_valid(form)

            groups = list(self.object.grupos_associados.values_list(
                'name', flat=True))
            globalrules.rules.groups_add_user(self.object.user, groups)

            return response

    class CreateView(MasterDetailCrudPermission.CreateView):
        form_class = OperadorAreaTrabalhoForm
        # TODO mostrar apenas usuários que não possuem grupo ou que são de
        # acesso social

        def form_valid(self, form):
            self.object = form.save(commit=False)
            oper = OperadorAreaTrabalho.objects.filter(
                user_id=self.object.user_id,
                areatrabalho_id=self.object.areatrabalho_id
            ).first()

            if oper:
                form._errors['user'] = ErrorList([_(
                    'Este Operador já está registrado '
                    'nesta Área de Trabalho.')])
                return self.form_invalid(form)

            response = super().form_valid(form)

            groups = list(self.object.grupos_associados.values_list(
                'name', flat=True))
            globalrules.rules.groups_add_user(self.object.user, groups)

            return response

    class DeleteView(MasterDetailCrudPermission.DeleteView):

        def post(self, request, *args, **kwargs):

            self.object = self.get_object()
            groups = list(
                self.object.grupos_associados.values_list('name', flat=True))
            globalrules.rules.groups_remove_user(self.object.user, groups)

            return MasterDetailCrudPermission.DeleteView.post(
                self, request, *args, **kwargs)


class PartidoCrud(DetailMasterCrud):
    help_text = 'partidos'
    model_set = 'filiacaopartidaria_set'
    model = Partido
    container_field_set = 'contato__workspace__operadores'
    # container_field = 'filiacoes_partidarias_set__contato__workspace__operadores'

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_set = ['contato_nome', ]

    class ListView(DetailMasterCrud.ListView):

        def get(self, request, *args, **kwargs):

            ws = AreaTrabalho.objects.filter(operadores=request.user).first()

            if ws and ws.parlamentar:
                filiacao_parlamentar = Filiacao.objects.filter(
                    parlamentar=ws.parlamentar)

                if filiacao_parlamentar.exists():
                    partido = filiacao_parlamentar.first().partido
                    return redirect(
                        reverse(
                            'sapl.parlamentares:partido_detail',
                            args=(partido.pk,)))

            """else:
                self.kwargs['queryset_liberar_sem_container'] = True"""

            return DetailMasterCrud.ListView.get(
                self, request, *args, **kwargs)

        """def get_queryset(self):
            queryset = CrudListView.get_queryset(self)
            if not self.request.user.is_authenticated():
                return queryset

            if 'queryset_liberar_sem_container' in self.kwargs and\
                    self.kwargs['queryset_liberar_sem_container']:
                return queryset

            if self.container_field:
                params = {}
                params[self.container_field] = self.request.user.pk
                return queryset.filter(**params)

            return queryset"""


class ImpressoEnderecamentoCrud(DetailMasterCrud):
    model = ImpressoEnderecamento

    class UpdateView(DetailMasterCrud.UpdateView):
        form_class = ImpressoEnderecamentoForm

    class CreateView(DetailMasterCrud.CreateView):
        form_class = ImpressoEnderecamentoForm
