from datetime import datetime
from distutils.util import strtobool
import io
import logging
from random import choice
from string import ascii_letters, digits
import tempfile
import zipfile

from braces.views import FormValidMessageMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.db.models import Max, Q
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.http import Http404, HttpResponse, JsonResponse
from django.http.response import HttpResponseRedirect, Http404
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils import timezone, formats
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView
from django.views.generic.base import RedirectView, TemplateView, ContextMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django_filters.views import FilterView
from weasyprint import HTML

from cmj.core.models import AreaTrabalho
from cmj.mixins import BtnCertMixin
from cmj.utils import ProcessoExterno
import sapl
from sapl.base.email_utils import do_envia_email_confirmacao
from sapl.base.models import Autor, CasaLegislativa, AppConfig
from sapl.base.signals import tramitacao_signal
from sapl.comissoes.models import Comissao
from sapl.crud.base import (Crud, CrudAux, MasterDetailCrud, make_pagination,
                            RP_LIST, RP_DETAIL,
                            PermissionRequiredContainerCrudMixin, CrudListView,
                            CrudDetailView)
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa, UnidadeTramitacao,\
    DocumentoAcessorio
from sapl.materia.views import gerar_pdf_impressos
from sapl.parlamentares.models import Legislatura, Parlamentar
from sapl.protocoloadm.forms import ProtocoloDocumentoAcessorioForm
from sapl.protocoloadm.models import Protocolo, DocumentoAdministrativo
from sapl.relatorios.views import relatorio_doc_administrativos, get_rodape, \
    make_pdf
from sapl.utils import (create_barcode, get_base_url, get_client_ip,
                        get_mime_type_from_file_extension, lista_anexados,
                        show_results_filter_set, mail_service_configured,
                        gerar_hash_arquivo, hash_sha512,
                        from_date_to_datetime_utc)

from .forms import (AcompanhamentoDocumentoForm, AnularProtocoloAdmForm,
                    DocumentoAcessorioAdministrativoForm,
                    DocumentoAdministrativoFilterSet,
                    DocumentoAdministrativoForm, FichaPesquisaAdmForm, FichaSelecionaAdmForm, ProtocoloDocumentForm,
                    ProtocoloFilterSet, ProtocoloMateriaForm,
                    TramitacaoAdmEditForm, TramitacaoAdmForm,
                    DesvincularDocumentoForm, DesvincularMateriaForm,
                    filtra_tramitacao_adm_destino_and_status,
                    filtra_tramitacao_adm_destino, filtra_tramitacao_adm_status,
                    AnexadoForm, AnexadoEmLoteFilterSet,
                    PrimeiraTramitacaoEmLoteAdmFilterSet,
                    TramitacaoEmLoteAdmForm,
                    TramitacaoEmLoteAdmFilterSet,
                    compara_tramitacoes_doc)
from .models import (AcompanhamentoDocumento, DocumentoAcessorioAdministrativo,
                     DocumentoAdministrativo, StatusTramitacaoAdministrativo,
                     TipoDocumentoAdministrativo, TramitacaoAdministrativo, Anexado)


# ProtocoloDocumentoCrud = Crud.build(Protocolo, '')
# FIXME precisa de uma chave diferente para o layout
# ProtocoloMateriaCrud = Crud.build(Protocolo, '')
@permission_required('protocoloadm.add_protocolo')
def recuperar_materia_protocolo(request):
    tipo = request.GET.get('tipo')
    ano = request.GET.get('ano')
    numero = request.GET.get('numero')
    logger = logging.getLogger(__name__)
    username = request.user.username
    try:
        logger.debug("user=" + username +
                     ". Tentando obter matéria com tipo={}, ano={} e numero={}.".format(tipo, ano, numero))
        materia = MateriaLegislativa.objects.get(
            tipo=tipo, ano=ano, numero=numero)
        autoria = materia.autoria_set.first()
        content = {'ementa': materia.ementa.strip(),
                   'ano': materia.ano, 'numero': materia.numero}
        if autoria:
            content.update({'autor': autoria.autor.pk,
                            'tipo_autor': autoria.autor.tipo.pk})
        response = JsonResponse(content)
    except Exception as e:
        logger.error("user=" + username + ". " + str(e))
        response = JsonResponse({'error': e})
    return response


def atualizar_numero_documento(request):
    if request.user.is_anonymous:
        raise Http404()
    tipo = TipoDocumentoAdministrativo.objects.get(pk=request.GET['tipo'])
    ano = request.GET['ano']

    param = {
        'tipo': tipo,
        'workspace__operadores': request.user,
        'ano': ano if ano else timezone.now().year
    }

    doc = DocumentoAdministrativo.objects.filter(**param).order_by(
        'tipo', 'ano', 'numero').values_list('numero', 'ano').last()

    if doc:
        response = JsonResponse({'numero': int(doc[0]) + 1,
                                 'ano': doc[1]})
    else:
        response = JsonResponse(
            {'numero': 1, 'ano': ano})

    return response


class CrudSemSubNavMixin(Crud):

    class SemSubNavMixin:

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = None
            return context

    class DetailView(SemSubNavMixin, Crud.DetailView):
        pass

    class UpdateView(SemSubNavMixin, Crud.UpdateView):
        pass

    class DeleteView(SemSubNavMixin, Crud.DeleteView):
        pass


class TipoDocumentoAdministrativoCrud(CrudSemSubNavMixin):
    model = TipoDocumentoAdministrativo
    help_topic = 'numeracao_docsacess'
    container_field = 'workspace__operadores'


class StatusTramitacaoAdministrativoCrud(CrudSemSubNavMixin):
    model = StatusTramitacaoAdministrativo
    help_topic = 'status_tramitacao'
    container_field = 'workspace__operadores'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['sigla', 'indicador', 'descricao']

    class ListView(Crud.ListView):
        ordering = 'sigla'


class DocumentoAdministrativoCrud(Crud):
    model = DocumentoAdministrativo
    help_topic = 'numeracao_docsacess'
    container_field = 'workspace__operadores'

    class QuerySetContainerPrivPubMixin(ContextMixin):
        is_contained = False

        def has_permission(self):
            """
            get_queryset faz os testes de permissão
            """
            return True

        def get_queryset(self):

            u = self.request.user
            crud = self.crud
            qs = crud.model.objects.all()

            param_tip_pub = {
                '%s__tipo' % '__'.join(crud.container_field.split('__')[:-1]):
                AreaTrabalho.TIPO_PUBLICO
            }

            param_user = {
                crud.container_field: self.request.user
            }

            if u.is_anonymous or not u.areatrabalho_set.exists():
                qs = qs.filter(**param_tip_pub)
            else:
                if u.has_perms(self.permission_required):
                    qs = qs.filter(**param_user)
                    self.is_contained = True
                else:
                    qs = qs.filter(**param_tip_pub)

            return qs

    class BaseMixin(Crud.BaseMixin):
        list_field_names = ['tipo', 'numero', 'ano', 'data',
                            'protocolo__numero', 'assunto',
                            'interessado', 'tramitacao', 'texto_integral']

        @property
        def search_url(self):
            namespace = self.model._meta.app_config.name
            return reverse('%s:%s' % (namespace, 'documentoadministrativo_list'))

        list_url = ''

        def get_initial(self):
            initial = {}

            try:
                initial['workspace'] = AreaTrabalho.objects.filter(
                    operadores=self.request.user.pk)[0]
            except:
                raise PermissionDenied(_('Sem permissão de Acesso!'))

            return initial

        @property
        def title(self):

            return _('%(sigla)s - %(tipo)s nº %(numero)s/%(ano)s %(interessado)s') % {
                'sigla': self.object.tipo.sigla,
                'tipo': self.object.tipo,
                'numero': self.object.numero,
                'ano': self.object.ano,
                'interessado': ('(%s)' % self.object.interessado)
                if self.object.interessado else ''
            }

    class CreateView(Crud.CreateView):
        form_class = DocumentoAdministrativoForm
        layout_key = None

        @property
        def cancel_url(self):
            return self.search_url

        def get_initial(self):
            initial = Crud.CreateView.get_initial(self)

            initial.update({
                'workspace': self.request.user.areatrabalho_set.first()
            })
            return initial

    class UpdateView(Crud.UpdateView):
        form_class = DocumentoAdministrativoForm
        layout_key = None

        def get_initial(self):
            if self.object.protocolo:
                p = self.object.protocolo
                return {'ano_protocolo': p.ano,
                        'numero_protocolo': p.numero, }

    class DeleteView(Crud.DeleteView):

        def get_success_url(self):
            return self.search_url

    class DetailView(BtnCertMixin, QuerySetContainerPrivPubMixin, DetailView):
        permission_required = ('protocoloadm.detail_documentoadministrativo',)

        layout_key = 'DocumentoAdministrativoDetail'

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)$'

        def get_context_data(self, **kwargs):
            context = DetailView.get_context_data(self, **kwargs)
            if self.object.epigrafe:
                context['title'] = self.object.epigrafe
            return context

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()

            try:
                download = request.GET.get('download', '')
                if download:
                    return self.monta_zip(download)
            except:
                messages.warning(request, 'Referência incorreta!')

            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

        def monta_zip(self, download):

            with tempfile.SpooledTemporaryFile(max_size=512000000) as tmp:

                with zipfile.ZipFile(tmp, 'w') as file:
                    das = DocumentoAdministrativo.objects.filter(
                        id__in=self.object.metadata['zipfile'][download]['da'])
                    daas = DocumentoAcessorioAdministrativo.objects.filter(
                        id__in=self.object.metadata['zipfile'][download]['daa'])
                    mls = MateriaLegislativa.objects.filter(
                        id__in=self.object.metadata['zipfile'][download]['ml'])

                    for d in das.order_by('id'):
                        if d.texto_integral:
                            file.write(
                                d.texto_integral.original_path,
                                arcname='DA-%s-%s' % (
                                    d.id,
                                    d.texto_integral.original_path.split(
                                        '/')[-1]))
                    for d in daas:
                        if d.arquivo:
                            file.write(
                                d.arquivo.original_path,
                                arcname='DA-%s-DAA-%s-%s' % (
                                    d.documento.id,
                                    d.id,
                                    d.arquivo.original_path.split(
                                        '/')[-1]))
                    for m in mls.order_by('id'):
                        if m.texto_original:
                            file.write(
                                m.texto_original.original_path,
                                arcname='ML-%s-%s' % (
                                    m.id,
                                    m.texto_original.original_path.split(
                                        '/')[-1]))

                tmp.seek(0)
                response = HttpResponse(tmp.read(),
                                        content_type='application/zip')

                response['Cache-Control'] = 'no-cache'
                response['Pragma'] = 'no-cache'
                response['Expires'] = 0
                response['Content-Disposition'] = \
                    'inline; filename=%s-%s-%s-%s.zip' % (
                        self.object.tipo.sigla,
                        self.object.numero,
                        self.object.ano,
                        download)

                return response

    class ListView(QuerySetContainerPrivPubMixin, FilterView):
        filterset_class = DocumentoAdministrativoFilterSet
        paginate_by = 10
        permission_required = ('protocoloadm.list_documentoadministrativo',)

        @classmethod
        def get_url_regex(cls):
            return r'^$'

        def get_filterset_kwargs(self, filterset_class):
            kwargs = super().get_filterset_kwargs(filterset_class)

            status_tramitacao = kwargs['request'].GET.get(
                'tramitacaoadministrativo__status')
            unidade_destino = kwargs['request'].GET.get(
                'tramitacaoadministrativo__unidade_tramitacao_destino')

            qs = kwargs['queryset']

            qs = qs.prefetch_related("documentoacessorioadministrativo_set",
                                     "tramitacaoadministrativo_set",
                                     "tipo",
                                     "tramitacaoadministrativo_set__status",
                                     "tramitacaoadministrativo_set__unidade_tramitacao_local",
                                     "tramitacaoadministrativo_set__unidade_tramitacao_destino")

            if status_tramitacao and unidade_destino:
                lista = filtra_tramitacao_adm_destino_and_status(status_tramitacao,
                                                                 unidade_destino)
                qs = qs.filter(id__in=lista).distinct()

            elif status_tramitacao:
                lista = filtra_tramitacao_adm_status(status_tramitacao)
                qs = qs.filter(id__in=lista).distinct()

            elif unidade_destino:
                lista = filtra_tramitacao_adm_destino(unidade_destino)
                qs = qs.filter(id__in=lista).distinct()

            if 'o' in self.request.GET and not self.request.GET['o']:
                qs = qs.order_by('-ano', '-data')

            kwargs.update({
                'queryset': qs,
                'workspace': AreaTrabalho.objects.areatrabalho_publica(
                ).first() if self.request.user.is_anonymous or
                not self.request.user.has_perms(self.permission_required)
                or not self.request.user.areatrabalho_set.exists()
                else self.request.user.areatrabalho_set.first()
            })
            return kwargs

        def get_context_data(self, *args, **kwargs):
            context = super().get_context_data(*args, **kwargs)

            if self.paginate_by:
                paginator = context['paginator']
                page_obj = context['page_obj']
                context['page_range'] = make_pagination(
                    page_obj.number, paginator.num_pages)
            context['title'] = _(
                'Pesquisa de Documentos Administrativos')
            context['bg_title'] = 'bg-aqua text-white'

            mostrar_anexos = self.request.GET.get('mostrar_anexos', '0')
            mostrar_anexos = strtobool(mostrar_anexos)

            context['mostrar_anexos'] = mostrar_anexos

            qr = self.request.GET.copy()

            if 'page' in qr:
                del qr['page']

            context['filter_url'] = (
                '&' + qr.urlencode()) if len(qr) > 0 else ''

            return context

        def get(self, request, *args, **kwargs):
            r = super().get(request, *args, **kwargs)
            # Se a pesquisa estiver quebrando com a paginação
            # Olhe esta função abaixo
            # Provavelmente você criou um novo campo no Form/FilterSet
            # Então a ordem da URL está diferente
            data = self.filterset.data
            if data and data.get('tipo') is not None:
                url = "&" + str(self.request.META['QUERY_STRING'])
                if url.startswith("&page"):
                    ponto_comeco = url.find('tipo=') - 1
                    url = url[ponto_comeco:]
            else:
                url = ''
            self.filterset.form.fields['o'].label = _('Ordenação')

            length = self.object_list.count()

            is_relatorio = url != '' and request.GET.get('relatorio', None)
            self.paginate_by = None if is_relatorio else self.paginate_by
            context = self.get_context_data(filter=self.filterset,
                                            filter_url=url,
                                            numero_res=length
                                            )
            context['show_results'] = show_results_filter_set(
                self.request.GET.copy())

            if is_relatorio:
                return relatorio_doc_administrativos(request, context)
            else:
                return self.render_to_response(context)


class DocumentoAcessorioAdministrativoCrud(MasterDetailCrud):
    model = DocumentoAcessorioAdministrativo
    parent_field = 'documento'
    help_topic = 'numeracao_docsacess'
    container_field = 'documento__workspace__operadores'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['nome', 'tipo',
                            'data', 'autor',
                            'assunto']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = DocumentoAcessorioAdministrativoForm

        def get_initial(self):
            initial = super().get_initial()
            initial['workspace'] = self.request.user.areatrabalho_set.first()
            return initial

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = DocumentoAcessorioAdministrativoForm

        def get_initial(self):
            initial = super().get_initial()
            initial['workspace'] = self.request.user.areatrabalho_set.first()
            return initial

    class DetailView(MasterDetailCrud.DetailView):
        is_contained = True

        def has_permission(self):
            return True

        def dispatch(self, request, *args, **kwargs):
            return DetailView.dispatch(self, request, *args, **kwargs)

        def get(self, request, *args, **kwargs):
            try:
                self.object = self.model.objects.get(pk=kwargs.get('pk'))
            except Exception as e:
                username = request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404

            context = DocumentoAcessorioAdministrativoCrud.DetailView.get_context_data(
                self, object=self.object)
            return self.render_to_response(context)

        def get_context_data(self, **kwargs):

            try:
                dp = kwargs['object'].documento
                kwargs['root_pk'] = dp.id

            except Exception as e:
                username = self.request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404()

            u = self.request.user

            if u.is_anonymous:
                if dp.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
                    raise Http404
            else:
                if dp.workspace.tipo == AreaTrabalho.TIPO_PUBLICO:
                    self.is_contained = dp.workspace == u.areatrabalho_set.first(
                    ) and u.has_perms(self.permission_required)
                    # if not self.is_contained and dp.workspace != u.areatrabalho_set.first():
                    #    raise Http404
                else:
                    # se não é público, se user faz parte do container e tem
                    # permissão visualização dos anexados
                    if dp.workspace == u.areatrabalho_set.first() and u.has_perms(self.permission_required):
                        self.is_contained = True
                    else:
                        raise Http404

            context = super(MasterDetailCrud.DetailView,
                            self).get_context_data(**kwargs)

            context[
                'title'] = 'Documento Principal: <small>(%s)</small>' % (
                    dp)
            return context

    class ListView(
            DocumentoAdministrativoCrud.QuerySetContainerPrivPubMixin,
            MasterDetailCrud.ListView):

        def dispatch(self, request, *args, **kwargs):
            return MasterDetailCrud.ListView.dispatch(self, request, *args, **kwargs)

        def get_queryset(self):
            qs = super().get_queryset()
            return qs.filter(documento_id=self.kwargs['pk'])

        def get_context_data(self, **kwargs):

            try:
                params = {'pk': kwargs['root_pk']}
                dp = DocumentoAdministrativo.objects.get(**params)

            except Exception as e:
                username = self.request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404()

            u = self.request.user

            if u.is_anonymous:
                if dp.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
                    raise Http404
            else:
                if dp.workspace.tipo == AreaTrabalho.TIPO_PUBLICO:
                    self.is_contained = dp.workspace == u.areatrabalho_set.first(
                    ) and u.has_perms(self.permission_required)
                    # if not self.is_contained and dp.workspace != u.areatrabalho_set.first():
                    #    raise Http404
                else:
                    # se não é público, se user faz parte do container e tem
                    # permissão visualização dos anexados
                    if dp.workspace == u.areatrabalho_set.first() and u.has_perms(self.permission_required):
                        self.is_contained = True
                    else:
                        raise Http404

            context = super(MasterDetailCrud.ListView,
                            self).get_context_data(**kwargs)

            context[
                'title'] = '%s a: <small>(%s)</small>' % (
                    context['title'],
                    dp)
            return context


class AnexadoCrud(MasterDetailCrud):
    model = Anexado
    parent_field = 'documento_principal'
    help_topic = 'documento_anexado'
    container_field = 'documento_principal__workspace__operadores'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['documento_anexado', 'data_anexacao']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = AnexadoForm

        def get_initial(self):
            initial = super().get_initial()

            initial['workspace'] = self.request.user.areatrabalho_set.first()
            return initial

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = AnexadoForm

        def get_initial(self):
            initial = super().get_initial()
            initial['tipo'] = self.object.documento_anexado.tipo.id
            initial['numero'] = self.object.documento_anexado.numero
            initial['ano'] = self.object.documento_anexado.ano

            initial['workspace'] = self.request.user.areatrabalho_set.first()

            return initial

    class DetailView(MasterDetailCrud.DetailView):
        is_contained = True

        @property
        def layout_key(self):
            return 'AnexadoDetail'

        def has_permission(self):
            return True

        def dispatch(self, request, *args, **kwargs):
            return DetailView.dispatch(self, request, *args, **kwargs)

        def get(self, request, *args, **kwargs):
            try:
                self.object = self.model.objects.get(pk=kwargs.get('pk'))
            except Exception as e:
                username = request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404

            context = AnexadoCrud.DetailView.get_context_data(
                self, object=self.object)
            return self.render_to_response(context)

        def get_context_data(self, **kwargs):

            try:
                dp = kwargs['object'].documento_principal
                kwargs['root_pk'] = dp.id

            except Exception as e:
                username = self.request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404()

            u = self.request.user

            if u.is_anonymous:
                if dp.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
                    raise Http404
            else:
                if dp.workspace.tipo == AreaTrabalho.TIPO_PUBLICO:
                    self.is_contained = dp.workspace == u.areatrabalho_set.first(
                    ) and u.has_perms(self.permission_required)
                    # if not self.is_contained and dp.workspace != u.areatrabalho_set.first():
                    #    raise Http404
                else:
                    # se não é público, se user faz parte do container e tem
                    # permissão visualização dos anexados
                    if dp.workspace == u.areatrabalho_set.first() and u.has_perms(self.permission_required):
                        self.is_contained = True
                    else:
                        raise Http404

            context = super(MasterDetailCrud.DetailView,
                            self).get_context_data(**kwargs)

            context[
                'title'] = 'Documento Principal: <small>(%s)</small>' % (
                    dp)
            return context

    class ListView(
            DocumentoAdministrativoCrud.QuerySetContainerPrivPubMixin,
            MasterDetailCrud.ListView):

        def dispatch(self, request, *args, **kwargs):
            return MasterDetailCrud.ListView.dispatch(self, request, *args, **kwargs)

        def get_queryset(self):
            qs = super().get_queryset()
            return qs.filter(documento_principal_id=self.kwargs['pk'])

        def get_context_data(self, **kwargs):

            try:
                params = {'pk': kwargs['root_pk']}
                dp = DocumentoAdministrativo.objects.get(**params)

            except Exception as e:
                username = self.request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404()

            u = self.request.user

            if u.is_anonymous:
                if dp.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
                    raise Http404
            else:
                if dp.workspace.tipo == AreaTrabalho.TIPO_PUBLICO:
                    self.is_contained = dp.workspace == u.areatrabalho_set.first(
                    ) and u.has_perms(self.permission_required)
                    # if not self.is_contained and dp.workspace != u.areatrabalho_set.first():
                    #    raise Http404
                else:
                    # se não é público, se user faz parte do container e tem
                    # permissão visualização dos anexados
                    if dp.workspace == u.areatrabalho_set.first() and u.has_perms(self.permission_required):
                        self.is_contained = True
                    else:
                        raise Http404

            context = super(MasterDetailCrud.ListView,
                            self).get_context_data(**kwargs)

            context[
                'title'] = '%s a: <small>(%s)</small>' % (
                    context['title'],
                    dp)
            return context


class DocumentoAnexadoEmLoteView(PermissionRequiredContainerCrudMixin, FilterView):
    filterset_class = AnexadoEmLoteFilterSet
    template_name = 'protocoloadm/em_lote/anexado.html'
    permission_required = ('protocoloadm.add_anexado',)
    container_field = 'workspace__operadores'
    model = DocumentoAdministrativo

    @property
    def cancel_url(self):
        return reverse('sapl.protocoloadm:anexado_list', kwargs={
            'pk': self.kwargs['pk']})

    @property
    def is_contained(self):
        return True

    def get_filterset_kwargs(self, filterset_class):
        kwargs = FilterView.get_filterset_kwargs(self, filterset_class)

        kwargs.update({
            'workspace': self.request.user.areatrabalho_set.first()
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(
            DocumentoAnexadoEmLoteView, self
        ).get_context_data(**kwargs)

        context['root_pk'] = self.kwargs['pk']

        context['subnav_template_name'] = 'protocoloadm/subnav.yaml'

        context['title'] = _('Documentos Anexados em Lote')

        # Verifica se os campos foram preenchidos
        if not self.request.GET.get('tipo', " "):
            msg = _('Por favor, selecione um tipo de documento.')
            messages.add_message(self.request, messages.ERROR, msg)

            if not self.request.GET.get('data_0', " ") or not self.request.GET.get('data_1', " "):
                msg = _('Por favor, preencha as datas.')
                messages.add_message(self.request, messages.ERROR, msg)

            return context

        if not self.request.GET.get('data_0', " ") or not self.request.GET.get('data_1', " "):
            msg = _('Por favor, preencha as datas.')
            messages.add_message(self.request, messages.ERROR, msg)
            return context

        qr = self.request.GET.copy()
        context['temp_object_list'] = context['object_list'].order_by(
            'numero', '-ano'
        )

        context['object_list'] = []
        for obj in context['temp_object_list']:
            if not obj.pk == int(context['root_pk']):
                documento_principal = DocumentoAdministrativo.objects.get(
                    id=context['root_pk'])
                documento_anexado = obj
                is_anexado = Anexado.objects.filter(documento_principal=documento_principal,
                                                    documento_anexado=documento_anexado).exists()
                if not is_anexado:
                    ciclico = False
                    anexados_anexado = Anexado.objects.filter(
                        documento_principal=documento_anexado)

                    while anexados_anexado and not ciclico:
                        anexados = []

                        for anexo in anexados_anexado:

                            if documento_principal == anexo.documento_anexado:
                                ciclico = True
                            else:
                                for a in Anexado.objects.filter(documento_principal=anexo.documento_anexado):
                                    anexados.append(a)

                        anexados_anexado = anexados

                    if not ciclico:
                        context['object_list'].append(obj)

        context['numero_res'] = len(context['object_list'])

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        return context

    def post(self, request, *args, **kwargs):
        marcados = request.POST.getlist('documento_id')

        data_anexacao = datetime.strptime(
            request.POST['data_anexacao'], "%d/%m/%Y"
        ).date()

        if request.POST['data_desanexacao'] == '':
            data_desanexacao = None
            v_data_desanexacao = data_anexacao
        else:
            data_desanexacao = datetime.strptime(
                request.POST['data_desanexacao'], "%d/%m/%Y"
            ).date()
            v_data_desanexacao = data_desanexacao

        if len(marcados) == 0:
            msg = _('Nenhum documento foi selecionado')
            messages.add_message(request, messages.ERROR, msg)

            if data_anexacao > v_data_desanexacao:
                msg = _('Data de anexação posterior à data de desanexação.')
                messages.add_message(request, messages.ERROR, msg)

            return self.get(request, self.kwargs)

        if data_anexacao > v_data_desanexacao:
            msg = _('Data de anexação posterior à data de desanexação.')
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, messages.ERROR, msg)

        principal = DocumentoAdministrativo.objects.get(pk=kwargs['pk'])
        for documento in DocumentoAdministrativo.objects.filter(id__in=marcados):
            anexado = Anexado()
            anexado.documento_principal = principal
            anexado.documento_anexado = documento
            anexado.data_anexacao = data_anexacao
            anexado.data_desanexacao = data_desanexacao
            anexado.save()

        msg = _('Documento(s) anexado(s).')
        messages.add_message(request, messages.SUCCESS, msg)

        success_url = reverse('sapl.protocoloadm:anexado_list', kwargs={
                              'pk': kwargs['pk']})
        return HttpResponseRedirect(success_url)


class TramitacaoAdmCrud(MasterDetailCrud):
    model = TramitacaoAdministrativo
    parent_field = 'documento'
    help_topic = 'unidade_tramitacao'
    container_field = 'documento__workspace__operadores'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['data_tramitacao', 'unidade_tramitacao_local',
                            'unidade_tramitacao_destino', 'status']

    class CreateView(MasterDetailCrud.CreateView):
        form_class = TramitacaoAdmForm
        logger = logging.getLogger(__name__)

        def get_success_url(self):
            return reverse('sapl.protocoloadm:tramitacaoadministrativo_list', kwargs={
                'pk': self.kwargs['pk']})

        def get_initial(self):
            initial = super(CreateView, self).get_initial()
            local = DocumentoAdministrativo.objects.get(
                pk=self.kwargs['pk']).tramitacaoadministrativo_set.order_by(
                '-data_tramitacao',
                '-id').first()

            if local:
                initial['unidade_tramitacao_local'
                        ] = local.unidade_tramitacao_destino.pk
            else:
                initial['unidade_tramitacao_local'] = ''
            initial['data_tramitacao'] = timezone.now().date()
            initial['ip'] = get_client_ip(self.request)
            initial['user'] = self.request.user
            initial['workspace'] = self.request.user.areatrabalho_set.first()
            return initial

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            username = self.request.user.username

            ultima_tramitacao = TramitacaoAdministrativo.objects.filter(
                documento_id=self.kwargs['pk']).order_by(
                '-data_tramitacao',
                '-timestamp',
                '-id').first()

            # TODO: Esta checagem foi inserida na issue #2027, mas é mesmo
            # necessária?
            if ultima_tramitacao:
                if ultima_tramitacao.unidade_tramitacao_destino:
                    context['form'].fields[
                        'unidade_tramitacao_local'].choices = [
                        (ultima_tramitacao.unidade_tramitacao_destino.pk,
                         ultima_tramitacao.unidade_tramitacao_destino)]
                else:
                    self.logger.error('user=' + username + '. Unidade de tramitação destino '
                                      'da última tramitação não pode ser vazia!')
                    msg = _('Unidade de tramitação destino '
                            ' da última tramitação não pode ser vazia!')
                    messages.add_message(self.request, messages.ERROR, msg)

            primeira_tramitacao = not(TramitacaoAdministrativo.objects.filter(
                documento_id=int(kwargs['root_pk'])).exists())

            # Se não for a primeira tramitação daquela matéria, o campo
            # não pode ser modificado
            if not primeira_tramitacao:
                context['form'].fields[
                    'unidade_tramitacao_local'].widget.attrs['readonly'] = True
            return context

        def form_valid(self, form):
            self.object = form.save()
            username = self.request.user.username
            try:
                tramitacao_signal.send(sender=TramitacaoAdministrativo,
                                       post=self.object,
                                       request=self.request)
            except Exception as e:
                self.logger.error('user=' + username + '. Tramitação criada, mas e-mail de acompanhamento de documento '
                                  'não enviado. A não configuração do servidor de e-mail '
                                  'impede o envio de aviso de tramitação. ' + str(e))
                msg = _('Tramitação criada, mas e-mail de acompanhamento '
                        'de documento não enviado. A não configuração do'
                        ' servidor de e-mail impede o envio de aviso de tramitação')
                messages.add_message(self.request, messages.WARNING, msg)
                return HttpResponseRedirect(self.get_success_url())
            return super().form_valid(form)

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = TramitacaoAdmEditForm
        logger = logging.getLogger(__name__)

        layout_key = 'TramitacaoAdministrativoUpdate'

        def get_initial(self):
            initial = super(UpdateView, self).get_initial()
            initial['ip'] = get_client_ip(self.request)
            initial['user'] = self.request.user
            initial['workspace'] = self.request.user.areatrabalho_set.first()

            return initial

        def form_valid(self, form):
            self.object = form.save()
            username = self.request.user.username
            try:
                tramitacao_signal.send(sender=TramitacaoAdministrativo,
                                       post=self.object,
                                       request=self.request)
            except Exception as e:
                self.logger.error('user=' + username + '. Tramitação criada, mas e-mail de acompanhamento de documento '
                                  'não enviado. A não configuração do servidor de e-mail '
                                  'impede o envio de aviso de tramitação. ' + str(e))
                msg = _('Tramitação criada, mas e-mail de acompanhamento '
                        'de documento não enviado. A não configuração do'
                        ' servidor de e-mail impede o envio de aviso de tramitação')
                messages.add_message(self.request, messages.WARNING, msg)
                return HttpResponseRedirect(self.get_success_url())
            return super().form_valid(form)

    class DetailView(MasterDetailCrud.DetailView):
        is_contained = True

        def has_permission(self):
            return True

        def dispatch(self, request, *args, **kwargs):
            return DetailView.dispatch(self, request, *args, **kwargs)

        def get(self, request, *args, **kwargs):
            try:
                self.object = self.model.objects.get(pk=kwargs.get('pk'))
            except Exception as e:
                username = request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404

            context = TramitacaoAdmCrud.DetailView.get_context_data(
                self, object=self.object)
            return self.render_to_response(context)

        def get_context_data(self, **kwargs):

            try:
                dp = kwargs['object'].documento
                kwargs['root_pk'] = dp.id

            except Exception as e:
                username = self.request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404()

            u = self.request.user

            if u.is_anonymous:
                if dp.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
                    raise Http404
            else:
                if dp.workspace.tipo == AreaTrabalho.TIPO_PUBLICO:
                    self.is_contained = dp.workspace == u.areatrabalho_set.first(
                    ) and u.has_perms(self.permission_required)
                    # if not self.is_contained and dp.workspace != u.areatrabalho_set.first():
                    #    raise Http404
                else:
                    # se não é público, se user faz parte do container e tem
                    # permissão visualização dos anexados
                    if dp.workspace == u.areatrabalho_set.first() and u.has_perms(self.permission_required):
                        self.is_contained = True
                    else:
                        raise Http404

            context = super(MasterDetailCrud.DetailView,
                            self).get_context_data(**kwargs)

            context['title'] = 'Tramitação de : <small>(%s)</small>' % (dp)
            return context

    class ListView(
            DocumentoAdministrativoCrud.QuerySetContainerPrivPubMixin,
            MasterDetailCrud.ListView):
        paginate_by = None

        def dispatch(self, request, *args, **kwargs):
            return MasterDetailCrud.ListView.dispatch(self, request, *args, **kwargs)

        def get_queryset(self):
            qs = super().get_queryset()
            return qs.filter(documento_id=self.kwargs['pk'])

        def get_context_data(self, **kwargs):

            try:
                params = {'pk': kwargs['root_pk']}
                dp = DocumentoAdministrativo.objects.get(**params)

            except Exception as e:
                username = self.request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404()

            u = self.request.user

            if u.is_anonymous:
                if dp.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
                    raise Http404
            else:
                if dp.workspace.tipo == AreaTrabalho.TIPO_PUBLICO:
                    self.is_contained = dp.workspace == u.areatrabalho_set.first(
                    ) and u.has_perms(self.permission_required)
                    # if not self.is_contained and dp.workspace != u.areatrabalho_set.first():
                    #    raise Http404
                else:
                    # se não é público, se user faz parte do container e tem
                    # permissão visualização dos anexados
                    if dp.workspace == u.areatrabalho_set.first() and u.has_perms(self.permission_required):
                        self.is_contained = True
                    else:
                        raise Http404

            context = super(MasterDetailCrud.ListView,
                            self).get_context_data(**kwargs)

            context[
                'title'] = 'Tramitações de: <small>(%s)</small>' % (
                    dp)
            return context

    class DeleteView(MasterDetailCrud.DeleteView):

        logger = logging.getLogger(__name__)

        def delete(self, request, *args, **kwargs):
            tramitacao = TramitacaoAdministrativo.objects.get(
                id=self.kwargs['pk'])
            documento = tramitacao.documento
            url = reverse(
                'sapl.protocoloadm:tramitacaoadministrativo_list',
                kwargs={'pk': documento.id})

            ultima_tramitacao = \
                documento.tramitacaoadministrativo_set.order_by(
                    '-data_tramitacao',
                    '-id').first()

            if tramitacao.pk != ultima_tramitacao.pk:
                username = request.user.username
                self.logger.error("user=" + username + ". Não é possível deletar a tramitação de pk={}. "
                                  "Somente a última tramitação (pk={}) pode ser deletada!."
                                  .format(tramitacao.pk, ultima_tramitacao.pk))
                msg = _('Somente a última tramitação pode ser deletada!')
                messages.add_message(request, messages.ERROR, msg)
                return HttpResponseRedirect(url)
            else:
                tramitacoes_deletar = [tramitacao.id]
                if documento.tramitacaoadministrativo_set.count() == 0:
                    documento.tramitacao = False
                    documento.save()
                tramitar_anexados = AppConfig.attr('tramitacao_documento')
                if tramitar_anexados:
                    docs_anexados = lista_anexados(documento, False)
                    for da in docs_anexados:
                        tram_anexada = da.tramitacaoadministrativo_set.last()
                        if compara_tramitacoes_doc(tram_anexada, tramitacao):
                            tramitacoes_deletar.append(tram_anexada.id)
                            if da.tramitacaoadministrativo_set.count() == 0:
                                da.tramitacao = False
                                da.save()
                TramitacaoAdministrativo.objects.filter(
                    id__in=tramitacoes_deletar).delete()

                return HttpResponseRedirect(url)


class PrimeiraTramitacaoEmLoteAdmView(PermissionRequiredMixin, FilterView):
    filterset_class = PrimeiraTramitacaoEmLoteAdmFilterSet
    template_name = 'protocoloadm/em_lote/tramitacaoadm.html'
    permission_required = ('protocoloadm.add_tramitacaoadministrativo',)

    primeira_tramitacao = True

    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(PrimeiraTramitacaoEmLoteAdmView,
                        self).get_context_data(**kwargs)

        context['subnav_template_name'] = 'protocoloadm/em_lote/subnav_em_lote.yaml'
        context['primeira_tramitacao'] = self.primeira_tramitacao

        # Verifica se os campos foram preenchidos
        if not self.filterset.form.is_valid():
            return context

        context['object_list'] = context['object_list'].order_by(
            'ano', 'numero')
        qr = self.request.GET.copy()

        form = TramitacaoEmLoteAdmForm()
        context['form'] = form

        if self.primeira_tramitacao:
            context['title'] = _('Primeira Tramitação em Lote')
            # Pega somente documentos que não possuem tramitação
            context['object_list'] = [obj for obj in context['object_list']
                                      if obj.tramitacaoadministrativo_set.all().count() == 0]
        else:
            context['title'] = _('Tramitação em Lote')
            context['form'].fields['unidade_tramitacao_local'].initial = UnidadeTramitacao.objects.get(
                id=qr['tramitacaoadministrativo__unidade_tramitacao_destino'])

        context['filter_url'] = ('&' + qr.urlencode()) if len(qr) > 0 else ''

        context['show_results'] = show_results_filter_set(qr)

        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        ip = get_client_ip(request)

        documentos_ids = request.POST.getlist('documentos')
        if not documentos_ids:
            msg = _("Escolha algum Documento para ser tramitado.")
            messages.add_message(request, messages.ERROR, msg)
            return self.get(request, self.kwargs)

        form = TramitacaoEmLoteAdmForm(request.POST,
                                       initial={'documentos': documentos_ids,
                                                'user': user, 'ip': ip})

        if form.is_valid():
            form.save()

            msg = _('Tramitação completa.')
            self.logger.info('user=' + user.username +
                             '. Tramitação completa.')
            messages.add_message(request, messages.SUCCESS, msg)
            return self.get_success_url()

        return self.form_invalid(form)

    def get_success_url(self):
        return HttpResponseRedirect(reverse('sapl.protocoloadm:primeira_tramitacao_em_lote_docadm'))

    def form_invalid(self, form, *args, **kwargs):
        for key, erros in form.errors.items():
            if not key == '__all__':
                [messages.add_message(
                    self.request, messages.ERROR, form.fields[key].label + ": " + e) for e in erros]
            else:
                [messages.add_message(self.request, messages.ERROR, e)
                 for e in erros]
        return self.get(self.request, kwargs, {'form': form})


class TramitacaoEmLoteAdmView(PrimeiraTramitacaoEmLoteAdmView):
    filterset_class = TramitacaoEmLoteAdmFilterSet

    primeira_tramitacao = False

    def get_context_data(self, **kwargs):
        context = super(TramitacaoEmLoteAdmView,
                        self).get_context_data(**kwargs)

        qr = self.request.GET.copy()

        context['primeira_tramitacao'] = self.primeira_tramitacao

        if ('tramitacao__status' in qr and
                'tramitacao__unidade_tramitacao_destino' in qr and
                qr['tramitacao__status'] and
                qr['tramitacao__unidade_tramitacao_destino']):
            lista = self.filtra_tramitacao_destino_and_status(
                qr['tramitacao__status'],
                qr['tramitacao__unidade_tramitacao_destino'])
            context['object_list'] = context['object_list'].filter(
                id__in=lista).distinct()

        return context

    def pega_ultima_tramitacao(self):
        return TramitacaoAdministrativo.objects.values(
            'documento_id').annotate(data_encaminhamento=Max(
                'data_encaminhamento'),
            id=Max('id')).values_list('id', flat=True)

    def filtra_tramitacao_status(self, status):
        lista = self.pega_ultima_tramitacao()
        return TramitacaoAdministrativo.objects.filter(
            id__in=lista,
            status=status).distinct().values_list('documento_id', flat=True)

    def filtra_tramitacao_destino(self, destino):
        lista = self.pega_ultima_tramitacao()
        return TramitacaoAdministrativo.objects.filter(
            id__in=lista,
            unidade_tramitacao_destino=destino).distinct().values_list(
                'documento_id', flat=True)

    def filtra_tramitacao_destino_and_status(self, status, destino):
        lista = self.pega_ultima_tramitacao()
        return TramitacaoAdministrativo.objects.filter(
            id__in=lista,
            status=status,
            unidade_tramitacao_destino=destino).distinct().values_list(
                'documento_id', flat=True)


class DesvincularDocumentoView(PermissionRequiredMixin, CreateView):
    template_name = 'protocoloadm/anular_protocoloadm.html'
    form_class = DesvincularDocumentoForm
    form_valid_message = _('Documento desvinculado com sucesso!')
    permission_required = ('protocoloadm.action_anular_protocolo',)

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo')

    def form_valid(self, form):
        documento = DocumentoAdministrativo.objects.get(numero=form.cleaned_data['numero'],
                                                        ano=form.cleaned_data['ano'],
                                                        tipo=form.cleaned_data['tipo'])
        documento.protocolo = None
        documento.save()
        return redirect(self.get_success_url())


class ProtocoloPesquisaView(PermissionRequiredMixin, FilterView):
    model = Protocolo
    filterset_class = ProtocoloFilterSet
    paginate_by = 10
    permission_required = ('protocoloadm.list_protocolo',)

    def get_filterset_kwargs(self, filterset_class):
        super(ProtocoloPesquisaView,
              self).get_filterset_kwargs(filterset_class)

        kwargs = {'data': self.request.GET or None}

        qs = self.get_queryset().order_by('ano', 'numero').distinct()

        if 'o' in self.request.GET and not self.request.GET['o']:
            qs = qs.order_by('-ano', '-numero')

        if not self.request.user.has_perm('protocoloadm.add_protocolo'):
            cts = ContentType.objects.get_for_models(
                MateriaLegislativa,
                DocumentoAcessorio)
            qs = qs.filter(
                conteudo_content_type__in=cts.values()
            )

        kwargs.update({
            'queryset': qs,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ProtocoloPesquisaView,
                        self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)

        context['title'] = _('Protocolo')

        return context

    def get(self, request, *args, **kwargs):
        super(ProtocoloPesquisaView, self).get(request)

        # Se a pesquisa estiver quebrando com a paginação
        # Olhe esta função abaixo
        # Provavelmente você criou um novo campo no Form/FilterSet
        # Então a ordem da URL está diferente
        data = self.filterset.data
        if data and data.get('numero') is not None:
            url = "&" + str(self.request.META['QUERY_STRING'])
            if url.startswith("&page"):
                ponto_comeco = url.find('numero=') - 1
                url = url[ponto_comeco:]
        else:
            url = ''

        self.filterset.form.fields['o'].label = _('Ordenação')

        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list,
                                        filter_url=url,
                                        numero_res=len(self.object_list)
                                        )

        context['show_results'] = show_results_filter_set(
            self.request.GET.copy())

        return self.render_to_response(context)


class ProtocoloListView(PermissionRequiredMixin, ListView):
    template_name = 'protocoloadm/protocolo_list.html'
    context_object_name = 'protocolos'
    model = Protocolo
    paginate_by = 10
    permission_required = ('protocoloadm.list_protocolo',)

    def get_queryset(self):
        kwargs = self.request.session['kwargs']
        return Protocolo.objects.filter(
            **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProtocoloListView, self).get_context_data(
            **kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = make_pagination(
            page_obj.number, paginator.num_pages)
        return context


class AnularProtocoloAdmView(PermissionRequiredMixin, CreateView):
    template_name = 'protocoloadm/anular_protocoloadm.html'
    form_class = AnularProtocoloAdmForm
    form_valid_message = _('Protocolo anulado com sucesso!')
    permission_required = ('protocoloadm.action_anular_protocolo',)

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo')

    def get_initial(self):
        initial_data = {}
        initial_data['user_anulacao'] = self.request.user.username
        initial_data['ip_anulacao'] = get_client_ip(self.request)
        return initial_data

    def form_valid(self, form):
        protocolo = Protocolo.objects.get(numero=form.cleaned_data['numero'],
                                          ano=form.cleaned_data['ano'])
        protocolo.anulado = True
        protocolo.justificativa_anulacao = (
            form.cleaned_data['justificativa_anulacao'])
        protocolo.user_anulacao = form.cleaned_data['user_anulacao']
        protocolo.ip_anulacao = form.cleaned_data['ip_anulacao']
        protocolo.timestamp_anulacao = timezone.now()
        protocolo.save()
        return redirect(self.get_success_url())


class ProtocoloDocumentoView(PermissionRequiredMixin,
                             FormValidMessageMixin,
                             CreateView):

    logger = logging.getLogger(__name__)

    template_name = "protocoloadm/protocolar_documento.html"
    form_class = ProtocoloDocumentForm
    form_valid_message = _('Protocolo cadastrado com sucesso!')
    permission_required = ('protocoloadm.add_protocolo',)

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo_mostrar',
                       kwargs={'pk': self.object.id})

    def get_initial(self):
        initial = super().get_initial()

        initial['user_data_hora_manual'] = self.request.user
        initial['ip_data_hora_manual'] = get_client_ip(self.request)
        initial['data'] = timezone.localdate(timezone.now())
        initial['hora'] = timezone.localtime(timezone.now())
        return initial

    @transaction.atomic
    def form_valid(self, form):
        protocolo = form.save(commit=False)
        username = self.request.user.username

        self.logger.debug("user=" + username +
                          ". Tentando obter sequência de numeração.")
        numeracao = AppConfig.objects.last(
        ).sequencia_numeracao_protocolo
        if not numeracao:
            self.logger.error("user=" + username + ". É preciso definir a sequencia de "
                              "numeração na tabelas auxiliares! ")
            msg = _('É preciso definir a sequencia de ' +
                    'numeração na tabelas auxiliares!')
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())

        if numeracao == 'A':
            numero = Protocolo.objects.filter(
                ano=timezone.now().year).aggregate(Max('numero'))
        elif numeracao == 'L':
            legislatura = Legislatura.objects.filter(
                data_inicio__year__lte=timezone.now().year,
                data_fim__year__gte=timezone.now().year).first()
            data_inicio = legislatura.data_inicio
            data_fim = legislatura.data_fim
            numero = Protocolo.objects.filter(
                data__gte=data_inicio,
                data__lte=data_fim).aggregate(
                Max('numero'))
        elif numeracao == 'U':
            numero = Protocolo.objects.all().aggregate(Max('numero'))

        protocolo.tipo_processo = '0'  # TODO validar o significado
        protocolo.anulado = False
        if not protocolo.numero:
            protocolo.numero = (
                numero['numero__max'] + 1) if numero['numero__max'] else 1
        elif protocolo.numero < (numero['numero__max'] + 1) if numero['numero__max'] else 0:
            msg = _('Número de protocolo deve ser maior que {}'.format(
                numero['numero__max']))
            self.logger.error(
                "user=" + username + ". Número de protocolo deve ser maior que {}.".format(numero['numero__max']))
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())
        protocolo.ano = timezone.now().year
        protocolo.assunto_ementa = self.request.POST['assunto']

        if form.cleaned_data['data_hora_manual'] == 'True':
            protocolo.timestamp = None
            protocolo.user_data_hora_manual = username
            protocolo.ip_data_hora_manual = get_client_ip(self.request)
        else:
            protocolo.data = None
            protocolo.hora = None
            protocolo.user_data_hora_manual = ''
            protocolo.ip_data_hora_manual = ''
        protocolo.tipo_conteudo_protocolado = form.cleaned_data['tipo_documento']

        protocolo.save()
        self.object = protocolo
        return redirect(self.get_success_url())


class ProtocoloDocumentoAcessorioView(PermissionRequiredMixin,
                                      FormValidMessageMixin,
                                      CreateView):

    logger = logging.getLogger(__name__)

    template_name = "protocoloadm/protocolar_documento_acessorio.html"
    form_class = ProtocoloDocumentoAcessorioForm
    form_valid_message = _('Protocolo cadastrado com sucesso!')
    permission_required = ('protocoloadm.add_protocolo',)

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo_mostrar',
                       kwargs={'pk': self.object.id})

    def get_initial(self):
        initial = super().get_initial()

        initial['user_data_hora_manual'] = self.request.user
        initial['ip_data_hora_manual'] = get_client_ip(self.request)
        initial['data'] = timezone.localdate(timezone.now())
        initial['hora'] = timezone.localtime(timezone.now())
        return initial

    @transaction.atomic
    def form_valid(self, form):
        protocolo = form.save(commit=False)
        username = self.request.user.username

        self.logger.debug("user=" + username +
                          ". Tentando obter sequência de numeração.")
        numeracao = AppConfig.objects.last(
        ).sequencia_numeracao_protocolo
        if not numeracao:
            self.logger.error("user=" + username + ". É preciso definir a sequencia de "
                              "numeração na tabelas auxiliares! ")
            msg = _('É preciso definir a sequencia de ' +
                    'numeração na tabelas auxiliares!')
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())

        if numeracao == 'A':
            numero = Protocolo.objects.filter(
                ano=timezone.now().year).aggregate(Max('numero'))
        elif numeracao == 'L':
            legislatura = Legislatura.objects.filter(
                data_inicio__year__lte=timezone.now().year,
                data_fim__year__gte=timezone.now().year).first()
            data_inicio = legislatura.data_inicio
            data_fim = legislatura.data_fim
            numero = Protocolo.objects.filter(
                data__gte=data_inicio,
                data__lte=data_fim).aggregate(
                Max('numero'))
        elif numeracao == 'U':
            numero = Protocolo.objects.all().aggregate(Max('numero'))

        protocolo.tipo_processo = '0'  # TODO validar o significado
        protocolo.anulado = False
        if not protocolo.numero:
            protocolo.numero = (
                numero['numero__max'] + 1) if numero['numero__max'] else 1
        elif protocolo.numero < (numero['numero__max'] + 1) if numero['numero__max'] else 0:
            msg = _('Número de protocolo deve ser maior que {}'.format(
                numero['numero__max']))
            self.logger.error(
                "user=" + username + ". Número de protocolo deve ser maior que {}.".format(numero['numero__max']))
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())
        protocolo.ano = timezone.now().year
        protocolo.assunto_ementa = self.request.POST['assunto']

        if form.cleaned_data['data_hora_manual'] == 'True':
            protocolo.timestamp = None
            protocolo.user_data_hora_manual = username
            protocolo.ip_data_hora_manual = get_client_ip(self.request)
        else:
            protocolo.data = None
            protocolo.hora = None
            protocolo.user_data_hora_manual = ''
            protocolo.ip_data_hora_manual = ''
        protocolo.tipo_conteudo_protocolado = form.cleaned_data['tipo_conteudo_protocolado']

        protocolo.save()
        self.object = protocolo
        return redirect(self.get_success_url())


class CriarDocumentoProtocolo(PermissionRequiredMixin, CreateView):
    template_name = "protocoloadm/criar_documento.html"
    form_class = DocumentoAdministrativoForm
    permission_required = ('protocoloadm.add_documentoadministrativo',)

    def get_initial(self):
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        return self.criar_documento(protocolo)

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo_mostrar',
                       kwargs={'pk': self.kwargs['pk']})

    def criar_documento(self, protocolo):
        curr_year = timezone.now().year

        numero_max = DocumentoAdministrativo.objects.filter(
            tipo=protocolo.tipo_conteudo_protocolado, ano=curr_year
        ).aggregate(Max('numero'))['numero__max']

        doc = {}
        doc['tipo'] = protocolo.tipo_conteudo_protocolado
        doc['ano'] = curr_year
        doc['data'] = timezone.now()
        doc['numero_protocolo'] = protocolo.numero
        doc['ano_protocolo'] = protocolo.ano
        doc['protocolo'] = protocolo.id
        doc['assunto'] = protocolo.assunto_ementa
        doc['interessado'] = protocolo.interessado
        doc['email'] = protocolo.email
        doc['numero'] = numero_max + 1 if numero_max else 1

        doc['workspace'] = self.request.user.areatrabalho_set.first()

        return doc


class ProtocoloRedirectConteudoView(PermissionRequiredMixin, RedirectView):
    permanent = False
    permission_required = ('protocoloadm.list_protocolo',)

    def get_redirect_url(self, *args, **kwargs):
        try:
            p = Protocolo.objects.get(pk=kwargs['pk'])
        except:
            raise Http404

        return reverse('%s:%s_detail' % (
            p.conteudo_protocolado._meta.app_config.name,
            p.conteudo_protocolado._meta.model_name
        ), args=(p.conteudo_protocolado.id,))


class SeloProtocoloMixin:

    def add_selo_protocolo(self):

        plugin_path = settings.PROJECT_DIR.child(
            'scripts').child(
            'java').child(
            'PluginSignPortalCMJ').child(
            'jar').child(
            'PluginSignPortalCMJ.jar')

        item = self.object.conteudo_protocolado
        p = self.object

        for field_file in item.FIELDFILE_NAME:
            file_path = getattr(item, field_file).path

            cmd = [
                'java -jar "{plugin}"',
                '{command}',
                '{x}',
                '{y}',
                '"{protocolo}"',
                '"{data_protocolo}"',
                '"{hora_protocolo}"',
                '"{sigla}"',
                '"{file}"',
                '"{certificado}"',
                '"{password}"',
                '"{data_selo}"',
                '"{hora_selo}"',
            ]
            cmd = ' '.join(cmd)

            cmd = cmd.format(
                **{
                    'plugin': plugin_path,
                    'command': 'cert_protocolo',
                    'x': 0,
                    'y': 0,
                    'protocolo': 'Protocolo: {}/{}'.format(p.numero, p.ano),
                    'data_protocolo': formats.date_format(
                        timezone.localtime(
                            p.timestamp) if p.timestamp else p.data,
                        'd/m/Y'
                    ),
                    'hora_protocolo': formats.date_format(
                        timezone.localtime(
                            p.timestamp) if p.timestamp else p.hora,
                        'H:i'
                    ),
                    'sigla': item.epigrafe_short,
                    'file': file_path,
                    'certificado': settings.CERT_PRIVATE_KEY_ID,
                    'password': settings.CERT_PRIVATE_KEY_ACCESS,
                    'data_selo': formats.date_format(timezone.localtime(), 'd/m/Y'),
                    'hora_selo': formats.date_format(timezone.localtime(), 'H:i'),
                }
            )

            # print(cmd)
            # return

            try:
                p = ProcessoExterno(cmd, self.logger)
                r = p.run(timeout=300)
                # if r is None:
                #    return None
                # if not r or r in (2, 6):
                #    return True
            except Exception as e:
                pass
        item.save()


class ProtocoloHomologarView(SeloProtocoloMixin, PermissionRequiredMixin, TemplateView):
    logger = logging.getLogger(__name__)

    permission_required = ('protocoloadm.action_homologar_protocolo',)

    def get(self, request, *args, **kwargs):
        self.object = Protocolo.objects.get(pk=self.kwargs['pk'])

        self.add_selo_protocolo()
        messages.info(request, _('Selo de Protocolo adicionado...'))

        return redirect(
            reverse('sapl.protocoloadm:protocolo_mostrar', kwargs={
                'pk': self.object.pk})
        )

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context['protocolo'] = self.object
        return context


class ProtocoloMostrarView(PermissionRequiredMixin, TemplateView):
    logger = logging.getLogger(__name__)

    template_name = "protocoloadm/protocolo_mostrar.html"
    permission_required = ('protocoloadm.detail_protocolo',)

    def get_context_data(self, **kwargs):

        context = super(ProtocoloMostrarView, self).get_context_data(**kwargs)
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        username = self.request.user.username

        if protocolo.tipo_materia:
            self.logger.debug(
                "user=" + username +
                ". Tentando obter objeto MateriaLegislativa com numero_protocolo={} e ano={}."
                .format(protocolo.numero, protocolo.ano))
            materia = MateriaLegislativa.objects.filter(
                numero_protocolo=protocolo.numero, ano=protocolo.ano)
            context['materia'] = materia
            if len(materia) > 1:
                msg = _('Foi encontrada mais de uma matéria com o mesmo número de protocolo e ano.'
                        ' Isso é um erro de uso!'
                        ' Reporte isso ao suporte para que seja corrigido.')
                messages.add_message(self.request, messages.ERROR, msg)
                self.logger.error(
                    "user=" + username + ". Objeto MateriaLegislativa com numero_protocolo={} e ano={}"
                                         " encontrado mais de um registro."
                                         " Erro relatado ao usuário.".format(protocolo.numero, protocolo.ano))

        if protocolo.tipo_documento:
            context[
                'documentos'] = protocolo.documentoadministrativo_set\
                                         .all().order_by('-ano', '-numero')

        context['protocolo'] = protocolo
        return context


class ComprovanteProtocoloView(PermissionRequiredMixin, TemplateView):

    template_name = "protocoloadm/comprovante.html"
    permission_required = ('protocoloadm.detail_protocolo',)

    def get_context_data(self, **kwargs):
        context = super(ComprovanteProtocoloView, self).get_context_data(
            **kwargs)
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        # numero is string, padd with zeros left via .zfill()
        base64_data = create_barcode(str(protocolo.numero).zfill(6))
        barcode = 'data:image/png;base64,{0}'.format(base64_data)

        autenticacao = _("** NULO **")

        if not protocolo.anulado:
            if protocolo.timestamp:
                data = protocolo.timestamp.strftime("%Y/%m/%d")
            else:
                data = protocolo.data.strftime("%Y/%m/%d")

            # data is not i18n sensitive 'Y-m-d' is the right format.
            autenticacao = str(protocolo.tipo_processo) + \
                data + str(protocolo.numero).zfill(6)

        if protocolo.tipo_materia:
            materia = MateriaLegislativa.objects.filter(
                numero_protocolo=protocolo.numero,
                ano=protocolo.ano).first()
            context['materia'] = materia

        context.update({"protocolo": protocolo,
                        "barcode": barcode,
                        "autenticacao": autenticacao})

        return context

    def get(self, request, *args, **kwargs):
        if 'send_mail' not in request.GET:
            return TemplateView.get(self, request, *args, **kwargs)

        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        protocolo.save()

        #messages.info(request, _('Email enviado com sucesso!'))

        return redirect(
            reverse('sapl.protocoloadm:protocolo_mostrar', kwargs={
                'pk': protocolo.pk})
        )


class ProtocoloMateriaView(PermissionRequiredMixin, CreateView):

    logger = logging.getLogger(__name__)

    template_name = "protocoloadm/protocolar_materia.html"
    form_class = ProtocoloMateriaForm
    form_valid_message = _('Matéria cadastrada com sucesso!')
    permission_required = ('protocoloadm.add_protocolo',)

    def get_success_url(self, protocolo):
        return reverse('sapl.protocoloadm:materia_continuar', kwargs={
            'pk': protocolo.pk})

    def get_initial(self):
        initial = super().get_initial()

        initial['user_data_hora_manual'] = self.request.user.username
        initial['ip_data_hora_manual'] = get_client_ip(self.request)
        initial['data'] = timezone.localdate(timezone.now())
        initial['hora'] = timezone.localtime(timezone.now())
        return initial

    @transaction.atomic
    def form_valid(self, form):
        protocolo = form.save(commit=False)
        username = self.request.user.username
        self.logger.debug("user=" + username +
                          ". Tentando obter sequência de numeração.")
        numeracao = AppConfig.objects.last(
        ).sequencia_numeracao_protocolo
        if not numeracao:
            self.logger.error("user=" + username + ". É preciso definir a sequencia de "
                              "numeração na tabelas auxiliares!")
            msg = _('É preciso definir a sequencia de ' +
                    'numeração na tabelas auxiliares!')
            messages.add_message(self.request, messages.ERROR, msg)
            return self.render_to_response(self.get_context_data())

        if numeracao == 'A':
            numero = Protocolo.objects.filter(
                ano=timezone.now().year).aggregate(Max('numero'))
        elif numeracao == 'L':
            legislatura = Legislatura.objects.filter(
                data_inicio__year__lte=timezone.now().year,
                data_fim__year__gte=timezone.now().year).first()
            data_inicio = legislatura.data_inicio
            data_fim = legislatura.data_fim

            data_inicio_utc = from_date_to_datetime_utc(data_inicio)
            data_fim_utc = from_date_to_datetime_utc(data_fim)

            numero = Protocolo.objects.filter(
                Q(data__isnull=False,
                  data__gte=data_inicio,
                  data__lte=data_fim) |
                Q(timestamp__isnull=False,
                  timestamp__gte=data_inicio_utc,
                  timestamp__lte=data_fim_utc) |
                Q(timestamp_data_hora_manual__isnull=False,
                  timestamp_data_hora_manual__gte=data_inicio_utc,
                  timestamp_data_hora_manual__lte=data_fim_utc,)
            ).aggregate(Max('numero'))

        elif numeracao == 'U':
            numero = Protocolo.objects.all().aggregate(Max('numero'))

        if numeracao is None:
            numero['numero__max'] = 0

        if not protocolo.numero:
            protocolo.numero = (
                numero['numero__max'] + 1) if numero['numero__max'] else 1
        if numero['numero__max']:
            if protocolo.numero < (numero['numero__max'] + 1):
                self.logger.error("user=" + username + ". Número de protocolo ({}) é menor que {}"
                                  .format(protocolo.numero, numero['numero__max']))
                msg = _('Número de protocolo deve ser maior que {}'.format(
                    numero['numero__max']))
                messages.add_message(self.request, messages.ERROR, msg)
                return self.render_to_response(self.get_context_data())
        protocolo.ano = timezone.now().year

        protocolo.tipo_protocolo = 0
        protocolo.tipo_processo = '1'  # TODO validar o significado
        protocolo.anulado = False

        if form.cleaned_data['autor']:
            protocolo.autor = form.cleaned_data['autor']

        protocolo.tipo_conteudo_protocolado = TipoMateriaLegislativa.objects.get(
            id=self.request.POST['tipo_materia'])

        protocolo.numero_paginas = self.request.POST['numero_paginas']
        protocolo.observacao = self.request.POST['observacao']
        protocolo.assunto_ementa = self.request.POST['assunto_ementa']

        if form.cleaned_data['data_hora_manual'] == 'True':
            protocolo.timestamp = None
            protocolo.user_data_hora_manual = username
            protocolo.ip_data_hora_manual = get_client_ip(self.request)
        else:
            protocolo.data = None
            protocolo.hora = None
            protocolo.user_data_hora_manual = ''
            protocolo.ip_data_hora_manual = ''
        protocolo.save()
        #
        #data = form.cleaned_data
        # if data['vincular_materia'] == 'True':
        #    materia = MateriaLegislativa.objects.get(ano=data['ano_materia'],
        #                                             numero=data['numero_materia'],
        #                                             tipo=data['tipo_materia'])
        #    materia.numero_protocolo = protocolo.numero
        #    materia.save()

        return redirect(self.get_success_url(protocolo))

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        autores_ativos = self.autores_ativos()

        autores = []
        autores.append(['0', '------'])
        for a in autores_ativos:
            autores.append([a.id, a.__str__()])

        context['form'].fields['autor'].choices = autores
        return context

    def autores_ativos(self):
        lista_parlamentares = Parlamentar.objects.filter(
            ativo=True).values_list('id', flat=True)
        model_parlamentar = ContentType.objects.get_for_model(Parlamentar)
        autor_parlamentar = Autor.objects.filter(
            content_type=model_parlamentar, object_id__in=lista_parlamentares)

        lista_comissoes = Comissao.objects.filter(Q(
            data_extincao__isnull=True) | Q(
            data_extincao__gt=timezone.now())).values_list('id', flat=True)
        model_comissao = ContentType.objects.get_for_model(Comissao)
        autor_comissoes = Autor.objects.filter(
            content_type=model_comissao, object_id__in=lista_comissoes)
        autores_outros = Autor.objects.exclude(
            content_type__in=[model_parlamentar, model_comissao])
        q = autor_parlamentar | autor_comissoes | autores_outros
        return q


class ProtocoloMateriaTemplateView(PermissionRequiredMixin, TemplateView):

    template_name = "protocoloadm/MateriaTemplate.html"
    permission_required = ('protocoloadm.detail_protocolo',)

    def get_context_data(self, **kwargs):
        context = super(ProtocoloMateriaTemplateView, self).get_context_data(
            **kwargs)
        protocolo = Protocolo.objects.get(pk=self.kwargs['pk'])
        context.update({'protocolo': protocolo})
        return context


class DesvincularMateriaView(PermissionRequiredMixin, FormView):
    template_name = 'protocoloadm/anular_protocoloadm.html'
    form_class = DesvincularMateriaForm
    form_valid_message = _('Matéria desvinculado com sucesso!')
    permission_required = ('protocoloadm.action_anular_protocolo',)

    def get_success_url(self):
        return reverse('sapl.protocoloadm:protocolo')

    def form_valid(self, form):
        materia = MateriaLegislativa.objects.get(numero=form.cleaned_data['numero'],
                                                 ano=form.cleaned_data['ano'],
                                                 tipo=form.cleaned_data['tipo'])
        materia.numero_protocolo = None
        materia.save()
        return redirect(self.get_success_url())


class ImpressosView(PermissionRequiredMixin, TemplateView):
    template_name = 'materia/impressos/impressos.html'
    permission_required = ('materia.can_access_impressos',)


class FichaPesquisaAdmView(PermissionRequiredMixin, FormView):
    form_class = FichaPesquisaAdmForm
    template_name = 'materia/impressos/impressos_form.html'
    permission_required = ('materia.can_access_impressos',)

    def form_valid(self, form):
        tipo_documento = form.data['tipo_documento']
        data_inicial = form.data['data_inicial']
        data_final = form.data['data_final']

        url = reverse('sapl.materia:impressos_ficha_seleciona_adm')
        url = url + '?tipo=%s&data_inicial=%s&data_final=%s' % (
            tipo_documento, data_inicial, data_final)

        return HttpResponseRedirect(url)


class FichaSelecionaAdmView(PermissionRequiredMixin, FormView):
    logger = logging.getLogger(__name__)
    form_class = FichaSelecionaAdmForm
    template_name = 'materia/impressos/impressos_form.html'
    permission_required = ('materia.can_access_impressos',)

    def get_context_data(self, **kwargs):
        if ('tipo' not in self.request.GET or
            'data_inicial' not in self.request.GET or
                'data_final' not in self.request.GET):
            return HttpResponseRedirect(reverse(
                'sapl.materia:impressos_ficha_pesquisa_adm'))

        context = super(FichaSelecionaAdmView, self).get_context_data(
            **kwargs)

        tipo = self.request.GET['tipo']
        data_inicial = datetime.strptime(
            self.request.GET['data_inicial'], "%d/%m/%Y").date()
        data_final = datetime.strptime(
            self.request.GET['data_final'], "%d/%m/%Y").date()

        documento_list = DocumentoAdministrativo.objects.filter(
            tipo=tipo,
            data__range=(data_inicial, data_final))
        context['quantidade'] = len(documento_list)
        documento_list = documento_list[:100]

        context['form'].fields['documento'].choices = [
            (d.id, str(d)) for d in documento_list]

        username = self.request.user.username

        if context['quantidade'] > 100:
            self.logger.info('user=' + username + '. Sua pesquisa (tipo={}, data_inicial={}, data_final={}) retornou mais do que '
                             '100 impressos. Por questões de '
                             'performance, foram retornados '
                             'apenas os 100 primeiros. Caso '
                             'queira outros, tente fazer uma '
                             'pesquisa mais específica'.format(tipo, data_inicial, data_final))
            messages.info(self.request, _('Sua pesquisa retornou mais do que '
                                          '100 impressos. Por questões de '
                                          'performance, foram retornados '
                                          'apenas os 100 primeiros. Caso '
                                          'queira outros, tente fazer uma '
                                          'pesquisa mais específica'))

        return context

    def form_valid(self, form):
        context = {}
        username = self.request.user.username

        try:
            self.logger.debug(
                "user=" + username + ". Tentando obter objeto DocumentoAdministrativo com id={}".format(form.data['documento']))
            documento = DocumentoAdministrativo.objects.get(
                id=form.data['documento'])
        except ObjectDoesNotExist:
            self.logger.error(
                "user=" + username + ". Este DocumentoAdministrativo não existe (id={}).".format(form.data['documento']))
            mensagem = _('Este Documento Administrativo não existe.')
            self.messages.add_message(self.request, messages.INFO, mensagem)

            return self.render_to_response(context)
        if len(documento.assunto) > 201:
            documento.assunto = documento.assunto[0:200] + '[...]'
        context['documento'] = documento

        return gerar_pdf_impressos(self.request, context,
                                   'materia/impressos/ficha_adm_pdf.html')


class AcompanhamentoConfirmarView(TemplateView):

    logger = logging.getLogger(__name__)

    def get_redirect_url(self, email):
        username = self.request.user.username
        self.logger.info(
            'user=' + username + '. Este documento está sendo acompanhado pelo e-mail: {}'.format(email))
        msg = _('Este documento está sendo acompanhado pelo e-mail: %s') % (
            email)
        messages.add_message(self.request, messages.SUCCESS, msg)
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):

        documento_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')
        username = request.user.username

        documento = DocumentoAdministrativo.objects.get(id=documento_id)

        if documento.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
            raise Http404

        try:
            self.logger.debug("user=" + username + ". Tentando obter objeto AcompanhamentoDocumento com documento_id={} e hash={}"
                              .format(documento_id, hash_txt))
            acompanhar = AcompanhamentoDocumento.objects.get(
                documento_id=documento_id,
                hash=hash_txt)
        except ObjectDoesNotExist as e:
            self.logger.error("user=" + username + ". " + str(e))
            raise Http404()
        # except MultipleObjectsReturned:
        # A melhor solução deve ser permitir que a exceção
        # (MultipleObjectsReturned) seja lançada e vá para o log,
        # pois só poderá ser causada por um erro de desenvolvimente

        acompanhar.confirmado = True
        acompanhar.save()

        return HttpResponseRedirect(self.get_redirect_url(acompanhar.email))


class AcompanhamentoExcluirView(TemplateView):

    logger = logging.getLogger(__name__)

    def get_success_url(self):
        username = self.request.user.username
        self.logger.info(
            "user=" + username + ". Você parou de acompanhar este Documento (pk={}).".format(self.kwargs['pk']))
        msg = _('Você parou de acompanhar este Documento.')
        messages.add_message(self.request, messages.INFO, msg)
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})

    def get(self, request, *args, **kwargs):
        documento_id = kwargs['pk']
        hash_txt = request.GET.get('hash_txt', '')
        username = request.user.username

        documento = DocumentoAdministrativo.objects.get(id=documento_id)

        if documento.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
            raise Http404

        try:
            self.logger.debug("user=" + username + ". Tentando obter AcompanhamentoDocumento com documento_id={} e hash={}."
                              .format(documento_id, hash_txt))
            AcompanhamentoDocumento.objects.get(documento_id=documento_id,
                                                hash=hash_txt).delete()
        except ObjectDoesNotExist:
            self.logger.error("user=" + username + ". AcompanhamentoDocumento com documento_id={} e hash={} não encontrado."
                              .format(documento_id, hash_txt))

        return HttpResponseRedirect(self.get_success_url())


class AcompanhamentoDocumentoView(CreateView):
    template_name = "protocoloadm/acompanhamento_documento.html"

    logger = logging.getLogger(__name__)

    def get_random_chars(self):
        s = ascii_letters + digits
        return ''.join(choice(s) for i in range(choice([6, 7])))

    def get(self, request, *args, **kwargs):
        if not mail_service_configured():
            self.logger.warning(_('Servidor de email não configurado.'))
            messages.error(request, _('Serviço de Acompanhamento de '
                                      'Documentos não foi configurado'))
            return redirect('/')

        pk = self.kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)

        if documento.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
            raise Http404

        return self.render_to_response(
            {'form': AcompanhamentoDocumentoForm(),
             'documento': documento})

    def post(self, request, *args, **kwargs):
        if not mail_service_configured():
            self.logger.warning(_('Servidor de email não configurado.'))
            messages.error(request, _('Serviço de Acompanhamento de '
                                      'Documentos não foi configurado'))
            return redirect('/')

        form = AcompanhamentoDocumentoForm(request.POST)
        pk = self.kwargs['pk']
        documento = DocumentoAdministrativo.objects.get(id=pk)

        if documento.workspace.tipo != AreaTrabalho.TIPO_PUBLICO:
            raise Http404

        if form.is_valid():
            email = form.cleaned_data['email']
            usuario = request.user

            hash_txt = self.get_random_chars()

            acompanhar = AcompanhamentoDocumento.objects.get_or_create(
                documento=documento,
                email=form.data['email'])

            # Se o segundo elemento do retorno do get_or_create for True
            # quer dizer que o elemento não existia
            if acompanhar[1]:
                acompanhar = acompanhar[0]
                acompanhar.hash = hash_txt
                acompanhar.usuario = usuario.username
                acompanhar.confirmado = False
                acompanhar.save()

                base_url = get_base_url(request)

                destinatario = AcompanhamentoDocumento.objects.get(
                    documento=documento,
                    email=email,
                    confirmado=False)
                casa = CasaLegislativa.objects.first()

                do_envia_email_confirmacao(base_url,
                                           casa,
                                           "documento",
                                           documento,
                                           destinatario)
                self.logger.info('user={}. Foi enviado um e-mail de confirmação. Confira sua caixa '
                                 'de mensagens e clique no link que nós enviamos para '
                                 'confirmar o acompanhamento deste documento.'.format(usuario.username))
                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                         de mensagens e clique no link que nós enviamos para \
                         confirmar o acompanhamento deste documento.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Se o elemento existir e o email não foi confirmado:
            # gerar novo hash e reenviar mensagem de email
            elif not acompanhar[0].confirmado:
                acompanhar = acompanhar[0]
                acompanhar.hash = hash_txt
                acompanhar.save()

                base_url = get_base_url(request)

                destinatario = AcompanhamentoDocumento.objects.get(
                    documento=documento,
                    email=email,
                    confirmado=False
                )

                casa = CasaLegislativa.objects.first()

                do_envia_email_confirmacao(base_url,
                                           casa,
                                           "documento",
                                           documento,
                                           destinatario)

                self.logger.info('user={}. Foi enviado um e-mail de confirmação. Confira sua caixa \
                                  de mensagens e clique no link que nós enviamos para \
                                  confirmar o acompanhamento deste documento.'.format(usuario.username))

                msg = _('Foi enviado um e-mail de confirmação. Confira sua caixa \
                        de mensagens e clique no link que nós enviamos para \
                        confirmar o acompanhamento deste documento.')
                messages.add_message(request, messages.SUCCESS, msg)

            # Caso esse Acompanhamento já exista
            # avisa ao usuário que esse documento já está sendo acompanhado
            else:
                self.logger.info('user=' + request.user.username +
                                 '. Este e-mail já está acompanhando esse documento (pk={}).'.format(pk))
                msg = _('Este e-mail já está acompanhando esse documento.')
                messages.add_message(request, messages.ERROR, msg)

                return self.render_to_response(
                    {'form': form,
                     'documento': documento,
                     })
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                {'form': form,
                 'documento': documento})

    def get_success_url(self):
        return reverse('sapl.protocoloadm:documentoadministrativo_detail',
                       kwargs={'pk': self.kwargs['pk']})
