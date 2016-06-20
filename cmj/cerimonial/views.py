from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils import six
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import ContextMixin
from django.views.generic.detail import DetailView
from django.views.generic.list import MultipleObjectMixin
from sapl.crispy_layout_mixin import get_field_display
from sapl.crud import base
from sapl.crud.base import Crud,  CrudDetailView, make_pagination,\
    CrudListView, CrudBaseMixin, CrudUpdateView,\
    CrudDeleteView, CrudCreateView
from sapl.crud.masterdetail import MasterDetailCrud

from cmj.cerimonial.models import StatusVisita, TipoTelefone, TipoEndereco,\
    TipoEmail, Parentesco, EstadoCivil, TipoAutoridade, TipoLocalTrabalho,\
    NivelInstrucao, Pessoa, Telefone, OperadoraTelefonia, Email


LIST, DETAIL, ADD, CHANGE, DELETE =\
    '.list_', '.detail_', '.add_', '.change_', '.delete_',


class PermissionRequiredWithAnonymousAcsessMixin(PermissionRequiredMixin):

    def get_permission_required(self):
        # Se permission_required é Vazio é permitido acesso anônimo
        if not self.permission_required:
            return ()

        if isinstance(self.permission_required, six.string_types):
            perms = (self.permission_required, )
        else:
            perms = self.permission_required
        return perms


class DetailMasterCrud(Crud):

    class BaseMixin(CrudBaseMixin):

        def __init__(self, **kwargs):
            self.app_label = self.crud.model._meta.app_label
            self.model_name = self.crud.model._meta.model_name
            if hasattr(self, 'permission_required') and\
                    self.permission_required:
                self.permission_required = tuple((
                    self.permission(pr) for pr in self.permission_required))

        def permission(self, radical):
            return '%s%s%s' % (self.app_label, radical, self.model_name)

        @property
        def list_url(self):
            return super().list_url\
                if self.request.user.has_perm(self.permission(DETAIL)) else ''

        @property
        def create_url(self):
            return super().create_url\
                if self.request.user.has_perm(self.permission(ADD)) else ''

        @property
        def update_url(self):
            return super().update_url\
                if self.request.user.has_perm(self.permission(CHANGE)) else ''

        @property
        def delete_url(self):
            return super().delete_url\
                if self.request.user.has_perm(self.permission(DELETE)) else ''

    class ListView(
            PermissionRequiredWithAnonymousAcsessMixin, CrudListView):
        permission_required = LIST,

    class CreateView(
            PermissionRequiredWithAnonymousAcsessMixin, CrudCreateView):
        permission_required = ADD,

    class UpDateView(
            PermissionRequiredWithAnonymousAcsessMixin, CrudUpdateView):
        permission_required = CHANGE,

    class DeleteView(
            PermissionRequiredWithAnonymousAcsessMixin, CrudDeleteView):
        permission_required = DELETE,

    class DetailView(
            PermissionRequiredWithAnonymousAcsessMixin,
            CrudDetailView, MultipleObjectMixin):
        permission_required = DETAIL,
        # Os colados nesta lista abaixo, nos models devem ter
        # ou atributos ou propertiers
        list_field_names_model_set = ['nome', ]

        paginate_by = 10
        no_entries_msg = _('Nenhum registro Associado.')

        def get_rows(self, object_list):
            return [self._as_row(obj) for obj in object_list]

        def get_headers(self):
            if not self.object_list:
                return []
            try:
                return [getattr(
                    self.object, self.crud.model_set).model._meta.get_field(
                    fieldname).verbose_name
                    for fieldname in self.list_field_names_model_set]
            except:
                return [getattr(
                    self.object,
                    self.crud.model_set).model._meta.verbose_name_plural]

        def url_model_set_name(self, suffix):
            return '%s_%s' % (
                getattr(self.object,
                        self.crud.model_set).model._meta.model_name,
                suffix)

        def resolve_model_set_url(self, suffix, args=None):
            namespace = getattr(
                self.object, self.crud.model_set).model._meta.app_config.name
            return reverse('%s:%s' % (
                namespace, self.url_model_set_name(suffix)),
                args=args)

        def _as_row(self, obj):
            try:
                return [(
                    get_field_display(obj, name)[1],
                    self.resolve_model_set_url(base.DETAIL, args=(obj.id,))
                    if i == 0 else None)
                    for i, name in enumerate(self.list_field_names_model_set)]
            except:
                return [(
                    getattr(obj, name),
                    self.resolve_model_set_url(base.DETAIL, args=(obj.id,))
                    if i == 0 else None)
                    for i, name in enumerate(self.list_field_names_model_set)]

        def get_object(self, queryset=None):
            return self.object

        def get(self, request, *args, **kwargs):
            self.object = self.model.objects.get(pk=kwargs.get('pk'))
            if self.crud.model_set:
                self.object_list = self.get_queryset()
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

        def get_queryset(self):
            # TODO implementar model_filter para filtrar por grandes escopos
            object_list = getattr(self.object, self.crud.model_set).all()
            return object_list

        def get_context_data(self, **kwargs):
            if self.crud.model_set:
                context = MultipleObjectMixin.get_context_data(self, **kwargs)
                if self.paginate_by:
                    page_obj = context['page_obj']
                    paginator = context['paginator']
                    context['page_range'] = make_pagination(
                        page_obj.number, paginator.num_pages)

                # rows
                object_list = context['object_list']
                context['headers'] = self.get_headers()
                context['rows'] = self.get_rows(object_list)

                context['NO_ENTRIES_MSG'] = self.no_entries_msg
            else:
                context = ContextMixin.get_context_data(self, **kwargs)
                if self.object:
                    context['object'] = self.object
                    context_object_name = self.get_context_object_name(
                        self.object)
                    if context_object_name:
                        context[context_object_name] = self.object
                context.update(kwargs)

            return context

    @classonlymethod
    def build(cls, _model, _model_set, _help_path):

        class ModelCrud(cls):
            model = _model
            model_set = _model_set
            help_path = _help_path

        ModelCrud.__name__ = '%sCrud' % _model.__name__
        return ModelCrud


class MasterDetailCrudPermission(MasterDetailCrud):

    class BaseMixin(MasterDetailCrud.BaseMixin):

        def __init__(self, **kwargs):
            self.app_label = self.crud.model._meta.app_label
            self.model_name = self.crud.model._meta.model_name
            if hasattr(self, 'permission_required') and\
                    self.permission_required:
                self.permission_required = tuple((
                    self.permission(pr) for pr in self.permission_required))

        def permission(self, radical):
            return '%s%s%s' % (self.app_label, radical, self.model_name)

        @property
        def list_url(self):
            return super().list_url\
                if self.request.user.has_perm(self.permission(LIST)) else ''

        @property
        def create_url(self):
            return super().create_url\
                if self.request.user.has_perm(self.permission(ADD)) else ''

        @property
        def update_url(self):
            return super().update_url\
                if self.request.user.has_perm(self.permission(CHANGE)) else ''

        @property
        def delete_url(self):
            return super().delete_url\
                if self.request.user.has_perm(self.permission(DELETE)) else ''

    class ListView(PermissionRequiredWithAnonymousAcsessMixin, MasterDetailCrud.ListView):
        permission_required = LIST,

        def get_context_data(self, **kwargs):
            context = MasterDetailCrud.ListView.get_context_data(
                self, **kwargs)

            parent_model = getattr(
                self.model, self.crud.parent_field).field.related_model

            parent_object = parent_model.objects.get(pk=kwargs['root_pk'])

            context['title'] = '%s (%s)' % (context['title'], parent_object)
            return context

    class CreateView(
            PermissionRequiredWithAnonymousAcsessMixin,
            MasterDetailCrud.CreateView):
        permission_required = ADD,

    class UpDateView(
            PermissionRequiredWithAnonymousAcsessMixin,
            MasterDetailCrud.UpdateView):
        permission_required = CHANGE,

    class DeleteView(
        PermissionRequiredWithAnonymousAcsessMixin,
            MasterDetailCrud.DeleteView):
        permission_required = DELETE,

    class DetailView(
            PermissionRequiredWithAnonymousAcsessMixin,
            MasterDetailCrud.DetailView):
        permission_required = DETAIL,
        template_name = 'crud/detail_detail.html'

        @property
        def detail_list_url(self):
            if self.request.user.has_perm(self.permission(LIST)):
                pk = getattr(self.get_object(), self.crud.parent_field).pk
                return self.resolve_url(base.LIST, args=(pk,))
            else:
                return ''

        @property
        def detail_create_url(self):
            if self.request.user.has_perm(self.permission(ADD)):
                pk = getattr(self.get_object(), self.crud.parent_field).pk
                return self.resolve_url(base.CREATE, args=(pk,))
            else:
                return ''


EstadoCivilCrud = DetailMasterCrud.build(
    EstadoCivil, 'pessoas_set', 'estadocivil')
NivelInstrucaoCrud = DetailMasterCrud.build(
    NivelInstrucao, 'pessoas_set', 'nivelinstrucao')

StatusVisitaCrud = DetailMasterCrud.build(StatusVisita, None, 'statusvisita')
TipoTelefoneCrud = DetailMasterCrud.build(TipoTelefone, None, 'tipotelefone')
TipoEnderecoCrud = DetailMasterCrud.build(TipoEndereco, None, 'tipoendereco')
TipoEmailCrud = DetailMasterCrud.build(TipoEmail, None, 'tipoemail')
ParentescoCrud = DetailMasterCrud.build(Parentesco, None, 'parentesco')
TipoAutoridadeCrud = DetailMasterCrud.build(
    TipoAutoridade, None, 'tipoautoriadade')
TipoLocalTrabalhoCrud = DetailMasterCrud.build(
    TipoLocalTrabalho, None, 'tipolocaltrabalho')


class PessoaCrud(DetailMasterCrud):
    model_set = None
    model = Pessoa

    class ListView(DetailMasterCrud.ListView):
        list_field_names_model_set = ['nome', ]
        permission_required = None


class OperadoraTelefoniaCrud(DetailMasterCrud):
    model_set = 'telefones_set'
    model = OperadoraTelefonia

    class DetailView(DetailMasterCrud.DetailView):
        list_field_names_model_set = ['numero_nome_pessoa', ]


class TelefoneCrud(MasterDetailCrudPermission):
    model = Telefone
    parent_field = 'pessoa'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['ddd', 'numero', 'tipo', 'operadora']


class EmailCrud(MasterDetailCrudPermission):
    model = Email
    parent_field = 'pessoa'

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):
        list_field_names = ['email', 'tipo', 'preferencial']

    class UpdateView(MasterDetailCrudPermission.UpdateView):

        def post(self, request, *args, **kwargs):
            response = TelefoneCrud.UpdateView.post(
                self, request, *args, **kwargs)

            if self.object.preferencial:
                Email.objects.filter(
                    pessoa_id=self.object.pessoa_id).exclude(
                    pk=self.object.pk).update(preferencial=False)
            return response
