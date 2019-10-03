
from builtins import property
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.utils import ErrorList
from django.http.response import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import formats, timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django_filters.views import FilterView
from rest_framework import viewsets, mixins
from rest_framework.authentication import SessionAuthentication,\
    BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from weasyprint import HTML

from cmj.core.forms import OperadorAreaTrabalhoForm, ImpressoEnderecamentoForm,\
    ListWithSearchForm
from cmj.core.models import Cep, TipoLogradouro, Logradouro, RegiaoMunicipal,\
    Distrito, Bairro, Trecho, AreaTrabalho, OperadorAreaTrabalho,\
    ImpressoEnderecamento, groups_remove_user, groups_add_user, Notificacao,\
    CertidaoPublicacao
from cmj.core.serializers import TrechoSearchSerializer, TrechoSerializer
from cmj.utils import normalize
from sapl.crud.base import Crud, CrudAux, MasterDetailCrud, RP_DETAIL, RP_LIST
from sapl.parlamentares.models import Partido, Filiacao


CepCrud = CrudAux.build(Cep, None, 'cep')
RegiaoMunicipalCrud = CrudAux.build(
    RegiaoMunicipal, None,  'regiao_municipal')
DistritoCrud = CrudAux.build(Distrito, None, 'distrito')
BairroCrud = CrudAux.build(Bairro, None, 'bairro')
TipoLogradouroCrud = CrudAux.build(
    TipoLogradouro, None, 'tipo_logradouro')
LogradouroCrud = CrudAux.build(Logradouro, None, 'logradouro')


def template_render(request, template_name):
    return render(request, template_name, {})


def chanel_index(request):
    return render(request, 'core/channel_index.html', {})


def chanel_room(request, room_name):
    return render(request, 'core/channel_room.html', {
        'room_name_json': mark_safe(json.dumps(room_name))
    })


def time_refresh_log_test(request):
    return render(request, 'core/time_refresh_log_test.html', {})


def app_vue_view(request):
    return render(request, 'app_vue.html')


class TrechoCrud(CrudAux):
    help_text = 'trecho'
    model = Trecho

    class BaseMixin(CrudAux.BaseMixin):
        list_field_names = [
            ('tipo', 'logradouro'), 'bairro', 'municipio', 'cep']

    class ListView(CrudAux.ListView):
        form_search_class = ListWithSearchForm

        def get(self, request, *args, **kwargs):
            """trechos = Trecho.objects.all()
            for t in trechos:
                t.search = str(t)
                t.save(auto_update_search=False)"""
            return CrudAux.ListView.get(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = CrudAux.ListView.get_context_data(
                self, **kwargs)
            context['title'] = _("Base de Cep's e Endereços")
            return context

    class CreateView(CrudAux.CreateView):

        def post(self, request, *args, **kwargs):
            response = super(CrudAux.CreateView, self).post(
                self, request, *args, **kwargs)

            # FIXME: necessário enquanto o metodo save não tratar fields  m2m
            self.object.search = str(self.object)
            self.object.save(auto_update_search=False)

            return response

    class UpdateView(CrudAux.UpdateView):

        def post(self, request, *args, **kwargs):
            response = super(CrudAux.UpdateView, self).post(
                self, request, *args, **kwargs)

            # FIXME: necessário enquanto o metodo save não tratar fields  m2m
            self.object.search = str(self.object)
            self.object.save(auto_update_search=False)

            return response


"""

class TrechoSearchView(PermissionRequiredMixin, FilterView):
    template_name = 'search/search.html'
    filterset_class = TrechoFilterSet
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

        return context"""


class TrechoJsonSearchView(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TrechoSearchSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    page_size = 0

    def get_queryset(self, *args, **kwargs):
        request = self.request
        queryset = Trecho.objects.all()

        if request.GET.get('q') is not None:
            query = normalize(str(request.GET.get('q')))

            query = query.split(' ')
            if query:
                q = Q()
                for item in query:
                    if not item:
                        continue
                    q = q & Q(search__icontains=item)

                if q:
                    queryset = queryset.filter(q)

        return queryset


class TrechoJsonView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TrechoSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    queryset = Trecho.objects.all()


class AreaTrabalhoCrud(Crud):
    model = AreaTrabalho
    model_set = 'operadorareatrabalho_set'

    class BaseMixin(Crud.BaseMixin):

        list_field_names = ['nome', 'tipo', 'parlamentar',
                            'ativo', 'operadores']

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            if 'subnav_template_name' not in context:
                context['subnav_template_name'] = 'core/subnav_areatrabalho.yaml'
            return context

    class DetailView(Crud.DetailView):
        list_field_names_set = ['user_name', ]

    class ListView(Crud.ListView):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context


class OperadorAreaTrabalhoCrud(MasterDetailCrud):
    parent_field = 'areatrabalho'
    model = OperadorAreaTrabalho
    help_path = 'operadorareatrabalho'

    class BaseMixin(MasterDetailCrud.BaseMixin):

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context[
                'subnav_template_name'] = 'core/subnav_areatrabalho.yaml'
            return context

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = OperadorAreaTrabalhoForm

        # TODO tornar operador readonly na edição
        def form_valid(self, form):
            old = OperadorAreaTrabalho.objects.get(pk=self.object.pk)

            groups = list(old.grupos_associados.values_list('name', flat=True))
            groups_remove_user(old.user, groups)

            response = super().form_valid(form)

            groups = list(self.object.grupos_associados.values_list(
                'name', flat=True))
            groups_add_user(self.object.user, groups)

            return response

    class CreateView(MasterDetailCrud.CreateView):
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
            groups_add_user(self.object.user, groups)

            return response

    class DeleteView(MasterDetailCrud.DeleteView):

        def post(self, request, *args, **kwargs):

            self.object = self.get_object()
            groups = list(
                self.object.grupos_associados.values_list('name', flat=True))
            groups_remove_user(self.object.user, groups)

            self.object.user.notificacao_set.filter(
                areatrabalho=self.object.areatrabalho,
                read=False).delete()

            return MasterDetailCrud.DeleteView.post(
                self, request, *args, **kwargs)


class PartidoCrud(Crud):
    help_text = 'partidos'
    model_set = 'filiacaopartidaria_set'
    model = Partido
    container_field_set = 'contato__workspace__operadores'
    # container_field = 'filiacoes_partidarias_set__contato__workspace__operadores'

    class DetailView(Crud.DetailView):
        list_field_names_set = ['contato_nome', ]

    class ListView(Crud.ListView):

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

            return Crud.ListView.get(
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


class ImpressoEnderecamentoCrud(Crud):
    model = ImpressoEnderecamento

    class UpdateView(Crud.UpdateView):
        form_class = ImpressoEnderecamentoForm

    class CreateView(Crud.CreateView):
        form_class = ImpressoEnderecamentoForm


class NotificacaoRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):

        try:
            obj = Notificacao.objects.get(pk=kwargs['pk'])
        except:
            raise Http404()

        if self.request.user != obj.user:
            raise Http404()
        obj.read = True
        obj.save()

        self.pattern_name = '%s:%s_detail' % (
            obj.content_object._meta.app_config.name,
            obj.content_object._meta.model_name
        )
        kwargs['pk'] = obj.content_object.pk
        url = RedirectView.get_redirect_url(self, *args, **kwargs)

        url += '#item-%s' % obj.content_object.pk
        return url


class CertidaoPublicacaoCrud(Crud):
    model = CertidaoPublicacao
    public = [RP_DETAIL, RP_LIST]

    DeleteView = None

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['id', 'created', 'content_type', 'content_object']

        @property
        def create_url(self):
            return ''

    class ListView(Crud.ListView):
        def split_bylen(self, item, maxlen):
            return [item[ind:ind + maxlen] for ind in range(0, len(item), maxlen)]

        def hook_content_object(self, *args, **kwargs):
            hash = args[0].hash_code  # self.split_bylen(args[0].hash_code, 64)

            return """%s<br><small>%s</small>""" % (
                args[1],
                args[0].content_object.__descr__), ''
            return """
            %s<br><small>%s</small><br>
            <button 
            class="hash_code btn btn-info"
            data-trigger="focus" 
            data-container="body"
            data-toggle="popover"
            data-placement="top" 
            title="Hash 512" 
            data-content="%s">Hash 512</button>""" % (
                args[1],
                args[0].content_object.__descr__,
                ''.join(hash)), ''

        def hook_header_content_object(self, **kwargs):
            return 'Documentos Certificados'

        def hook_header_content_type(self, **kwargs):
            return 'Tipo do Documento'

        def hook_header_id(self, **kwargs):
            return 'Certidão'

        def hook_id(self, *args, **kwargs):
            return '%06d' % int(args[1]), args[2]

        def hook_header_created(self, **kwargs):
            return 'Data/Hora'

        def hook_created(self, *args, **kwargs):
            return '{}'.format(
                formats.date_format(
                    timezone.template_localtime(args[0].created), 'd/m/Y \à\s H:i')
            ), args[2]

    class DetailView(DetailView):
        slug_field = 'hash_code'

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)$'

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()

            context = self.get_context_data(object=self.object)

            return self.certidao_publicacao(request, context)

        def get_context_data(self, **kwargs):
            context = DetailView.get_context_data(self, **kwargs)
            context['print'] = 'print' in self.request.GET
            context['content_object_url'] = self.content_object_url()
            return context

        def certidao_publicacao(self, request, context):
            base_url = request.build_absolute_uri()

            html_template = render_to_string(
                'core/certidao_publicacao.html', context)

            html = HTML(base_url=base_url, string=html_template)
            main_doc = html.render(stylesheets=[])
            pdf_file = main_doc.write_pdf()

            response = HttpResponse(content_type='application/pdf;')
            response['Content-Disposition'] = 'inline; filename=relatorio.pdf'
            response['Content-Transfer-Encoding'] = 'binary'
            response.write(pdf_file)

            return response

        def content_object_url(self):
            cert = self.object
            co = cert.content_object

            link = reverse(
                'sapl.api:%s-%s' % (
                    co._meta.model_name,
                    cert.field_name.replace('_', '-')
                ),
                kwargs={'pk': co.id}
            )

            urls = {
                'original': '%s%s?original' % (settings.SITE_URL, link),
                'ocr': '%s%s?ocr' % (settings.SITE_URL, link),
            }

            return urls

    class CreateView(Crud.CreateView):

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<content_type>\d+)/create/(?P<pk>\d+)/(?P<field_name>\w+)$'

        def get(self, request, *args, **kwargs):

            if self.certidao_generate():
                return redirect(
                    reverse('cmj.core:certidaopublicacao_detail',
                            kwargs={'pk': self.content_object.certidao.pk})
                )

            else:
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _('Não foi possível gerar certidão!'))

                return redirect(
                    reverse('%s:%s_detail' % (
                        self.content_object._meta.app_config.name,
                        self.content_object._meta.model_name),
                        kwargs={'pk': self.content_object.pk})
                )

        def certidao_generate(self):

            model = ContentType.objects.get_for_id(
                self.kwargs['content_type']).model_class()

            object = self.content_object = model.objects.get(
                pk=self.kwargs['pk'])

            if object.certidao:
                return True

            if not getattr(object, self.kwargs['field_name']):
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _('Documento sem Arquivo.'))
                return False

            u = self.request.user

            try:
                CertidaoPublicacao.gerar_certidao(
                    u, object, self.kwargs['field_name'])
            except Exception as e:
                return False

            return True
