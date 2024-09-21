
from builtins import property
import collections
import io
import json
import logging
import re

from django import template
from django.conf import settings
from django.conf.locale import ru
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db.models import Q
from django.forms.utils import ErrorList
from django.http.response import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils import formats, timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import RedirectView, TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.static import serve as view_static_server
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
    CertidaoPublicacao, Bi
from cmj.core.serializers import TrechoSearchSerializer, TrechoSerializer
from cmj.mixins import PluginSignMixin
from cmj.utils import normalize
from sapl.api.mixins import ResponseFileMixin
from sapl.crud.base import Crud, CrudAux, MasterDetailCrud, RP_DETAIL, RP_LIST
from sapl.parlamentares.models import Partido, Filiacao
from sapl.utils import get_mime_type_from_file_extension


logger = logging.getLogger(__name__)


CepCrud = CrudAux.build(Cep, None, 'cep')
RegiaoMunicipalCrud = CrudAux.build(
    RegiaoMunicipal, None,  'regiao_municipal')
DistritoCrud = CrudAux.build(Distrito, None, 'distrito')
BairroCrud = CrudAux.build(Bairro, None)
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


def app_vue_view(request, slug=None):
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
        paginate_by = 100

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = ''
            return context

        def hook_header_ativo(self):
            return "At. Ativa"

        def hook_operadores(self, *args, **kwargs):
            lista_html = ''
            for u in args[0].operadores.all():
                lista_html += '<li>{}<br><small>{}</small></li>'.format(
                    u.get_full_name(), u.email)

            return '<ul>{}</ul>'.format(lista_html), ''


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

    class ListView(MasterDetailCrud.ListView):

        def hook_user(self, *args, **kwargs):
            u = args[0].user
            lista_html = '{}<br><small>{}</small></li>'.format(
                u.get_full_name(), u.email)

            return lista_html, args[2]

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
        paginate_by = 100

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
            if not self.request.user.is_authenticated:
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
        obj.not_send_mail = True  # Não envia email no post_save
        obj.save()

        self.pattern_name = '%s:%s_detail' % (
            obj.content_object._meta.app_config.name,
            obj.content_object._meta.model_name
        )
        kwargs['pk'] = obj.content_object.pk
        url = RedirectView.get_redirect_url(self, *args, **kwargs)

        url += '#item-%s' % obj.content_object.pk
        return url


class SeloCertidaoMixin(PluginSignMixin):

    def add_selo_certidao(self, original2copia=False):

        cert = self.object

        compression = False
        #compression = False if not autor else autor.tipo.descricao == 'Executivo'

        for field_file in cert.FIELDFILE_NAME:
            if original2copia:
                paths = '{},{}'.format(
                    getattr(cert, field_file).original_path,
                    getattr(cert, field_file).path,
                )

            else:
                paths = getattr(cert, field_file).path

            cmd = self.cmd_mask

            params = {
                'plugin': self.plugin_path,
                'comando': 'selo_certidao',
                'in_file': paths,
                'certificado': settings.CERT_PRIVATE_KEY_ID,
                'password': settings.CERT_PRIVATE_KEY_ACCESS,
                'data_ocorrencia': formats.date_format(
                    timezone.localtime(cert.created),
                    'd/m/Y'
                ),
                'hora_ocorrencia': formats.date_format(
                    timezone.localtime(cert.created),
                    'H:i'
                ),
                'data_comando': formats.date_format(timezone.localtime(), 'd/m/Y'),
                'hora_comando': formats.date_format(timezone.localtime(), 'H:i'),
                'titulopre': 'Câmara Municipal de Jataí - Estado de Goiás',
                'titulo': '___',
                'titulopos': '___',
                'x': int(self.request.GET.get('x', 80)),
                'y': int(self.request.GET.get('y', 86)),
                'w': 80,
                'h': 20,
                'cor': "0, 76, 64, 255",
                'compression': compression,
                'debug': False  # settings.DEBUG
            }
            cmd = cmd.format(
                **params
            )

            self.run(cmd)

            del params['plugin']
            del params['in_file']
            del params['certificado']
            del params['password']
            del params['debug']
            del params['comando']
            cert.metadata['selos'] = {'selo_certidao': params}

            # print(cmd)
            # return

        cert.save()


class CertidaoPublicacaoCrud(Crud):
    model = CertidaoPublicacao
    public = [RP_DETAIL, RP_LIST]

    DeleteView = None

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['id', 'created',
                            'content_type', 'content_object', 'signs']

        @property
        def create_url(self):
            return ''

    class ListView(Crud.ListView):

        def has_permission(self):
            return True

        paginate_by = 100

        def split_bylen(self, item, maxlen):
            return [item[ind:ind + maxlen] for ind in range(0, len(item), maxlen)]

        def hook_header_signs(self, **kwargs):
            return 'Assinaturas Digitais'

        def hook_signs(self, *args, **kwargs):

            obj = args[0].content_object
            sig_tuples = []
            try:
                signs = obj.metadata['signs']
                for fn, sigs in signs.items():
                    for sig in sigs['signs']:
                        sig_tuples.append(sig)

                sign_template = template.loader.get_template(
                    'core/sign_widget.html')
                context = {}
                context['signs'] = sig_tuples
                rendered = sign_template.render(context, self.request)

                return rendered, ''

            except Exception as e:
                return args[1], args[2]

        def hook_content_object(self, *args, **kwargs):

            hash = args[0].hash_code  # self.split_bylen(args[0].hash_code, 64)

            if hasattr(args[0].content_object, 'anexo_de') and\
                    args[0].content_object.anexo_de.exists():
                vinculo = f'Vínculo com: {args[0].content_object.anexo_de.first()}'
            else:
                vinculo = ''

            return """%s<br>
            <small>%s</small><br>
            <small><i>%s</i></small>""" % (
                args[1],
                args[0].content_object.__descr__,
                vinculo
            ), ''

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
            cert = '%06d' % int(args[1])
            if args[0].cancelado:
                return f'''{cert}<br>
                    Certidão Cancelada<br>
                    <small>Documento Substituído</small>
                    ''', ''
            if not self.request.user.is_superuser or args[0].certificado:
                return cert, args[2]

            return f'''
                <a href="{args[2]}">{cert}</a>
                <a href="{args[2]}?certificar" class="btn btn-link">Certificar</a>
            ''', ''

        def hook_header_created(self, **kwargs):
            return 'Data/Hora'

        def hook_created(self, *args, **kwargs):
            return '{}'.format(
                formats.date_format(
                    timezone.template_localtime(args[0].created), 'd/m/Y \à\s H:i')
            ), args[2]

    class DetailView(DetailView, SeloCertidaoMixin):
        slug_field = 'hash_code'

        @classmethod
        def get_url_regex(cls):
            return r'^/(?P<pk>\d+)$'

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()
            if self.object.cancelado:
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _('Certidão Cancelada!'))
                return redirect(
                    reverse('cmj.core:certidaopublicacao_list',
                            kwargs={})
                )

            context = self.get_context_data(object=self.object)

            if 'certificar' in request.GET and request.user.is_superuser:
                return self.certidao_digital_de_publicacao(request, context)

            return self.certidao_publicacao(request, context)

        @property
        def vinculo(self):

            # self.split_bylen(args[0].hash_code, 64)
            hash = self.object.hash_code

            if hasattr(self.object.content_object, 'anexo_de') and\
                    self.object.content_object.anexo_de.exists():
                vinculo = f'Vínculo com: {self.object.content_object.anexo_de.first()}'
            else:
                vinculo = ''
            return vinculo

        def get_context_data(self, **kwargs):
            context = DetailView.get_context_data(self, **kwargs)
            if 'print' not in self.request.GET:
                context['print'] = ''
            else:
                print_value = self.request.GET.get('print', '1')
                print_value = print_value or '1'
                context['print'] = f"{print_value}cm"
            context['content_object_url'] = self.content_object_url()
            return context

        def certidao_digital_de_publicacao(self, request, context):
            self.certidao_publicacao(
                request,
                context,
                template='core/certidao_digital_publicacao.html',
                only_persist=True
            )

            self.add_selo_certidao()

            response = HttpResponse(
                self.object.certificado, content_type='application/pdf;')
            response['Content-Disposition'] = f'inline; filename=cert-cmj-{self.object.id}.pdf'
            response['Content-Transfer-Encoding'] = 'binary'

            return response

        def certidao_publicacao(self, request, context, template='', only_persist=False):

            if self.object.certificado and \
                    not 'certificar' in request.GET and \
                    not request.user.is_superuser and \
                    not only_persist:

                with open(self.object.certificado.path, 'rb') as f:
                    fpdf = f.read()
            else:
                base_url = request.build_absolute_uri()
                html_template = render_to_string(
                    template if template else 'core/certidao_publicacao.html',
                    context)
                html = HTML(base_url=base_url, string=html_template)
                main_doc = html.render(stylesheets=[])
                fpdf = main_doc.write_pdf()

                if only_persist:
                    self.object.certificado = ContentFile(
                        fpdf, name=f'cert-cmj-{self.object.id}.pdf')

                    self.object.save()
                    return

            response = HttpResponse(fpdf, content_type='application/pdf;')
            response['Content-Disposition'] = f'inline; filename=cert-cmj-{self.object.id}.pdf'
            response['Content-Transfer-Encoding'] = 'binary'

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
                'ocr': '%s%s' % (settings.SITE_URL, link),
            }

            return urls

    class CreateView(Crud.CreateView):

        @classmethod
        def get_url_regex(cls):
            return r'^/(?P<content_type>\d+)/create/(?P<pk>\d+)/(?P<field_name>\w+)$'

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

            certidao = object.certidao

            if certidao and not self.request.user.is_superuser:
                return True

            if not getattr(object, self.kwargs['field_name']):
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _('Documento sem Arquivo.'))
                return False

            u = self.request.user

            try:
                certidao.cancelado = True
                certidao.certificado = None
                certidao.save()
                CertidaoPublicacao.gerar_certidao(
                    u, object, self.kwargs['field_name'])
            except Exception as e:
                return False

            return True


class BiView(ListView):
    model = Bi
    paginate_by = None

    @property
    def title(self):
        return 'B'

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)

        context['global'] = self.get_global()
        context['producao_anual'] = self.get_producao_anual()

        return context

    def get_global(self):
        qs = self.get_queryset()

        g = {'Páginas Digitalizadas': {
            'count': 0,
            'color': ''
        }}

        for i in qs:

            results = i.results

            for user, ru in results.items():  # ru -> result user

                for model, rm in ru.items():  # rm -> result model
                    if model not in g:
                        g[model] = {
                            'count': 0,
                            'color': re.sub('\s', '', normalize(model.lower()))
                        }
                    for ano, ra in rm.items():  # rm -> result anos
                        try:
                            g[model]['count'] += ra.get('total',
                                                        ra.get('count', 0))
                            g['Páginas Digitalizadas']['count'] += ra.get(
                                'paginas', 0)
                        except Exception as e:
                            print(ra)

        g = filter(lambda x: x[1]['count'] > 500, g.items())
        return g

    def get_producao_anual(self):
        qs = self.get_queryset()

        pa = {}

        for i in qs:
            if i.ano not in pa:
                pa[i.ano] = {
                    'documentos': 0,
                    'paginas': 0,
                    'tramitacao': 0
                }

            results = i.results

            for user, ru in results.items():  # ru -> result user

                for model, rm in ru.items():  # rm -> result model
                    for ano, ra in rm.items():  # rm -> result anos
                        pa[i.ano]['documentos'] += ra.get('total', 0)
                        pa[i.ano]['paginas'] += ra.get('paginas', 0)
                        pa[i.ano]['tramitacao'] += ra.get('tramitacao', 0)

        sum_documentos = 0
        sum_paginas = 0
        sum_tramitacao = 0
        for k, v in pa.items():
            sum_documentos += v['documentos']
            sum_paginas += v['paginas']
            sum_tramitacao += v['tramitacao']

        per_d_max = 0
        per_p_max = 0
        per_t_max = 0
        for k, v in pa.items():
            v['largura'] = {
                'documentos': v['documentos'] / sum_documentos * 100,
                'paginas': v['paginas'] / sum_paginas * 100,
                'tramitacao': v['tramitacao'] / sum_paginas * 100
            }

            if v['documentos'] > per_d_max:
                per_d_max = v['documentos']

            if v['paginas'] > per_p_max:
                per_p_max = v['paginas']

            if v['tramitacao'] > per_t_max:
                per_t_max = v['tramitacao']

        for k, v in pa.items():
            v['largura'] = {
                'documentos': (v['documentos'] * (100 / per_d_max)) if per_d_max else 0,
                'paginas': (v['paginas'] * (100 / per_p_max)) if per_p_max else 0,
                'tramitacao': (v['tramitacao'] * (100 / per_t_max)) if per_t_max else 0
            }

        pa = list(pa.items())
        pa.sort(key=lambda row: row[0])
        pa.reverse()
        return pa


class MediaPublicView(View):

    def get(self, request, *args, **kwargs):

        path = kwargs['path']

        if 'private' in path:
            raise Http404

        if settings.DEBUG:
            return view_static_server(
                request,
                path,
                document_root=settings.MEDIA_ROOT
            )

        file_path = f'{settings.MEDIA_ROOT}/{path}'
        file_name = path.split('/')[-1]
        ext = file_name.split('.')[-1]

        mime = get_mime_type_from_file_extension(file_name)

        # if mime.endswith('ext') and :

        mime = 'image/png'

        response = HttpResponse(content_type='')
        response['Content-Disposition'] = (
            'inline; filename="%s"' % file_name)

        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0

        response['X-Accel-Redirect'] = "/mediaredirect/{0}".format(
            path
        )

        return response
