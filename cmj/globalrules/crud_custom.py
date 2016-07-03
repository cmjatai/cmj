from compressor.utils.decorators import cached_property
from django.conf.urls import url
from django.contrib.auth import logout
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.shortcuts import redirect
from django.utils import six
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import ContextMixin
from django.views.generic.list import MultipleObjectMixin
from sapl.crispy_layout_mixin import get_field_display
from sapl.crud import base
from sapl.crud.base import Crud, CrudBaseMixin, CrudListView, CrudCreateView,\
    CrudUpdateView, CrudDeleteView, CrudDetailView, make_pagination

from cmj.cerimonial.models import Perfil
from cmj.globalrules.globalrules import GROUP_SOCIAL_USERS


LIST, DETAIL, ADD, CHANGE, DELETE =\
    '.list_', '.detail_', '.add_', '.change_', '.delete_',


class PermissionRequiredContainerCrudMixin(PermissionRequiredMixin):

    def has_permission(self):
        perms = self.get_permission_required()
        return self.request.user.has_perms(perms) if perms[0] else True

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()

        if 'pk' in kwargs:
            params = {'pk': kwargs['pk']}

            if self.container_field:
                params[self.container_field] = request.user.pk

            if not self.model.objects.filter(**params).exists():
                raise Http404()

        return super(PermissionRequiredMixin, self).dispatch(
            request, *args, **kwargs)

    @cached_property
    def container_field(self):
        if not hasattr(self.crud, 'container_field'):
            self.crud.container_field = ''
        return self.crud.container_field

    @cached_property
    def container_field_set(self):
        if not hasattr(self.crud, 'container_field_set'):
            self.crud.container_field_set = ''
        return self.crud.container_field_set

    @cached_property
    def is_contained(self):
        return self.container_field_set or self.container_field


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
                if self.request.user.has_perm(self.permission(LIST)) else ''

        @property
        def detail_url(self):
            return super().detail_url\
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
            PermissionRequiredContainerCrudMixin, CrudListView):
        permission_required = (LIST, )

        def get_queryset(self):
            queryset = CrudListView.get_queryset(self)
            if not self.request.user.is_authenticated():
                return queryset

            if self.container_field:
                params = {}
                params[self.container_field] = self.request.user.pk
                return queryset.filter(**params)

            return queryset

        def dispatch(self, request, *args, **kwargs):
            return PermissionRequiredMixin.dispatch(
                self, request, *args, **kwargs)

    class CreateView(
            PermissionRequiredContainerCrudMixin, CrudCreateView):
        permission_required = (ADD, )

        def dispatch(self, request, *args, **kwargs):
            return super(PermissionRequiredMixin, self).dispatch(
                request, *args, **kwargs)

        def form_valid(self, form):
            self.object = form.save(commit=False)
            try:
                self.object.owner = self.request.user
                self.object.modifier = self.request.user

                if self.container_field:
                    container = self.container_field.split('__')

                    if len(container) > 1:
                        if hasattr(self.object, container[0]):
                            container_model = getattr(
                                self.model, container[0]).field.related_model

                            params = {}
                            params['__'.join(
                                container[1:])] = self.request.user.pk

                            container_data = container_model.objects.filter(
                                **params).first()

                            setattr(self.object, container[0], container_data)
            except:
                pass

            return super().form_valid(form)

    class UpdateView(
            PermissionRequiredContainerCrudMixin, CrudUpdateView):
        permission_required = (CHANGE, )

        def form_valid(self, form):
            self.object = form.save(commit=False)
            try:
                self.object.modifier = self.request.user
            except:
                pass

            return super().form_valid(form)

    class DeleteView(
            PermissionRequiredContainerCrudMixin, CrudDeleteView):
        permission_required = (DELETE, )

    class DetailView(
            PermissionRequiredContainerCrudMixin,
            CrudDetailView, MultipleObjectMixin):
        permission_required = (DETAIL, )
        # Os colados nesta lista abaixo, nos models devem ter,
        # ou atributos, ou propertiers
        list_field_names_set = ['nome', ]

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
                    for fieldname in self.list_field_names_set]
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
                    for i, name in enumerate(self.list_field_names_set)]
            except:
                return [(
                    getattr(obj, name),
                    self.resolve_model_set_url(base.DETAIL, args=(obj.id,))
                    if i == 0 else None)
                    for i, name in enumerate(self.list_field_names_set)]

        def get_object(self, queryset=None):
            return self.object

        def get(self, request, *args, **kwargs):
            self.object = self.model.objects.get(pk=kwargs.get('pk'))
            if hasattr(self.crud, 'model_set') and self.crud.model_set:
                self.object_list = self.get_queryset()
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

        def get_queryset(self):
            queryset = getattr(self.object, self.crud.model_set).all()

            if not self.request.user.is_authenticated():
                return queryset

            if self.container_field_set:
                params = {}
                params[self.container_field_set] = self.request.user.pk
                return queryset.filter(**params)

            return queryset

        def get_context_data(self, **kwargs):
            if hasattr(self.crud, 'model_set') and self.crud.model_set:
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


class MasterDetailCrudPermission(DetailMasterCrud):

    class BaseMixin(DetailMasterCrud.BaseMixin):

        @property
        def list_url(self):
            return self.resolve_url(base.LIST, args=(self.kwargs['pk'],))\
                if self.request.user.has_perm(self.permission(LIST)) else ''

        @property
        def create_url(self):
            return self.resolve_url(base.CREATE, args=(self.kwargs['pk'],))\
                if self.request.user.has_perm(self.permission(ADD)) else ''

        @property
        def detail_url(self):
            return super().detail_url\
                if self.request.user.has_perm(self.permission(DETAIL)) else ''

        @property
        def update_url(self):
            return super().update_url\
                if self.request.user.has_perm(self.permission(CHANGE)) else ''

        @property
        def delete_url(self):
            return super().delete_url\
                if self.request.user.has_perm(self.permission(DELETE)) else ''

        def get_context_data(self, **kwargs):
            obj = getattr(self, 'object', None)
            if obj:
                root_pk = getattr(obj, self.crud.parent_field).pk
            else:
                root_pk = self.kwargs['pk']  # in list and create
            kwargs.setdefault('root_pk', root_pk)
            return super(CrudBaseMixin,
                         self).get_context_data(**kwargs)

    class ListView(DetailMasterCrud.ListView):
        permission_required = LIST,

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)/%s$' % cls.model._meta.model_name

        def dispatch(self, request, *args, **kwargs):

            return PermissionRequiredMixin.dispatch(
                self, request, *args, **kwargs)

        def get_context_data(self, **kwargs):
            context = CrudListView.get_context_data(
                self, **kwargs)

            parent_model = getattr(
                self.model, self.crud.parent_field).field.related_model

            params = {'pk': kwargs['root_pk']}

            if self.container_field:
                container = self.container_field.split('__')
                if len(container) > 1:
                    params['__'.join(container[1:])] = self.request.user.pk

            try:
                parent_object = parent_model.objects.get(**params)
            except:
                raise Http404()

            context['title'] = '%s (%s)' % (context['title'], parent_object)
            return context

        def get_queryset(self):
            qs = super(CrudListView, self).get_queryset()

            kwargs = {self.crud.parent_field: self.kwargs['pk']}

            if self.container_field:
                kwargs[self.container_field] = self.request.user.pk

            return qs.filter(**kwargs)

    class CreateView(DetailMasterCrud.CreateView):
        permission_required = ADD,

        def dispatch(self, request, *args, **kwargs):
            return PermissionRequiredMixin.dispatch(
                self, request, *args, **kwargs)

        @classmethod
        def get_url_regex(cls):
            return r'^(?P<pk>\d+)/%s/create$' % cls.model._meta.model_name

        def get_form(self, form_class=None):
            form = super(CrudCreateView,
                         self).get_form(self.form_class)
            field = self.model._meta.get_field(self.crud.parent_field)
            parent = field.related_model.objects.get(pk=self.kwargs['pk'])

            setattr(form.instance, self.crud.parent_field, parent)
            return form

    class UpdateView(DetailMasterCrud.UpdateView):
        permission_required = CHANGE,

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)/edit$' % cls.model._meta.model_name

    class DeleteView(DetailMasterCrud.DeleteView):
        permission_required = DELETE,

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)/delete$' % cls.model._meta.model_name

        def get_success_url(self):
            pk = getattr(self.get_object(), self.crud.parent_field).pk
            return self.resolve_url(base.LIST, args=(pk,))

    class DetailView(DetailMasterCrud.DetailView):
        permission_required = DETAIL,
        template_name = 'crud/detail_detail.html'

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)$' % cls.model._meta.model_name

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

    @classonlymethod
    def build(cls, model, parent_field, help_path):
        crud = super(MasterDetailCrudPermission, cls).build(model, help_path)
        crud.parent_field = parent_field
        return crud


class PerfilAbstractCrud(DetailMasterCrud):
    model_set = None
    model = Perfil

    class Meta:
        abstract = True

    class BaseMixin(DetailMasterCrud.BaseMixin):

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
            return ''

        @property
        def create_url(self):
            return ''

        @property
        def detail_url(self):
            return self.resolve_url(base.DETAIL)\
                if self.request.user.has_perm(self.permission(ADD)) else ''

        @property
        def update_url(self):
            return self.resolve_url(base.UPDATE)\
                if self.request.user.has_perm(self.permission(CHANGE)) else ''

        @property
        def delete_url(self):
            return self.resolve_url(base.DELETE)\
                if self.request.user.has_perm(self.permission(DELETE)) else ''

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = 'cerimonial/subnav_perfil.yaml'
            return context

    class DetailView(DetailMasterCrud.DetailView):

        def get(self, request, *args, **kwargs):

            try:
                self.object = self.model.objects.for_user(request.user)
            except:
                return redirect(reverse('cmj.cerimonial:perfil_create'))

            return self.render_to_response(self.get_context_data(object=self.object))

    class UpdateView(DetailMasterCrud.UpdateView):

        def get(self, request, *args, **kwargs):

            try:
                self.object = self.model.objects.for_user(request.user)
            except:
                return redirect(reverse('cmj.cerimonial:perfil_create'))

            context = self.get_context_data()
            return self.render_to_response(context)

        def post(self, request, *args, **kwargs):

            try:
                self.object = self.model.objects.for_user(request.user)
            except:
                return redirect(reverse('cmj.cerimonial:perfil_create'))

            kwargs['pk'] = self.object.pk
            self.kwargs['pk'] = self.object.pk

            return DetailMasterCrud.UpdateView.post(self, request, *args, **kwargs)

    class DeleteView(DetailMasterCrud.DeleteView):

        def check_permission(self):
            if self.object.perfil_user.groups.all().exclude(
                    name=GROUP_SOCIAL_USERS).exists():
                raise PermissionDenied(
                    _('Você não possui permissão '
                      'para se autoremover do Portal!'))

        def get(self, request, *args, **kwargs):

            try:
                self.object = self.model.objects.for_user(request.user)
            except:
                return redirect(reverse('cmj.cerimonial:perfil_create'))

            self.check_permission()

            return self.render_to_response(self.get_context_data())

        def post(self, request, *args, **kwargs):

            try:
                self.object = self.model.objects.for_user(request.user)
            except:
                return redirect(reverse('cmj.cerimonial:perfil_create'))

            self.check_permission()
            self.object.perfil_user.delete()

            logout(request)

            return redirect('/login')

    class CreateView(DetailMasterCrud.CreateView):

        def get(self, request, *args, **kwargs):
            if request.user.is_authenticated():
                if request.user.contatos_set.exists():
                    return redirect(reverse('cmj.cerimonial:perfil_detail'))

            return DetailMasterCrud.CreateView.get(self, request, *args, **kwargs)

        def form_valid(self, form):
            fv = DetailMasterCrud.CreateView.form_valid(self, form)

            self.object.perfil_user = self.request.user
            self.object.save()
            return fv

    @classonlymethod
    def get_urls(cls):
        def _add_base(view):
            class CrudViewWithBase(cls.BaseMixin, view):
                model = cls.model
                help_path = cls.help_path
                crud = cls
            CrudViewWithBase.__name__ = view.__name__
            return CrudViewWithBase

        CrudCreateView = _add_base(cls.CreateView)
        CrudDetailView = _add_base(cls.DetailView)
        CrudUpdateView = _add_base(cls.UpdateView)
        CrudDeleteView = _add_base(cls.DeleteView)

        return [
            url(regex, view.as_view(), name=view.url_name(suffix))
            for regex, view, suffix in [
                (CrudListView.get_url_regex(), CrudDetailView, base.DETAIL),
                (CrudCreateView.get_url_regex(), CrudCreateView, base.CREATE),
                (r'^edit$', CrudUpdateView, base.UPDATE),
                (r'^delete$', CrudDeleteView, base.DELETE),
            ]]


class PerfilDetailCrudPermission(MasterDetailCrudPermission):

    class BaseMixin(MasterDetailCrudPermission.BaseMixin):

        def perfil(self):
            try:
                perfil = Perfil.objects.for_user(self.request.user)
            except:
                return redirect(reverse('cmj.cerimonial:perfil_create'))
            return perfil

        @property
        def list_url(self):
            return self.resolve_url(base.LIST)\
                if self.request.user.has_perm(self.permission(LIST)) else ''

        @property
        def create_url(self):
            return self.resolve_url(base.CREATE)\
                if self.request.user.has_perm(self.permission(ADD)) else ''

        @property
        def detail_url(self):
            return self.resolve_url(
                base.DETAIL, args=(self.object.id,))\
                if self.request.user.has_perm(self.permission(DETAIL)) else ''

        @property
        def update_url(self):
            return self.resolve_url(
                base.UPDATE, args=(self.object.id,))\
                if self.request.user.has_perm(self.permission(CHANGE)) else ''

        @property
        def delete_url(self):
            return self.resolve_url(
                base.DELETE, args=(self.object.id,))\
                if self.request.user.has_perm(self.permission(DELETE)) else ''

        def get_context_data(self, **kwargs):
            obj = getattr(self, 'object', None)
            if obj:
                root_pk = getattr(obj, self.crud.parent_field).pk
            else:
                perfil = self.perfil()
                if isinstance(perfil, Perfil):
                    root_pk = perfil.pk
                else:
                    return perfil

            kwargs.setdefault('root_pk', root_pk)

            context = super(MasterDetailCrudPermission.BaseMixin,
                            self).get_context_data(**kwargs)

            context['subnav_template_name'] = 'cerimonial/subnav_perfil.yaml'
            return context

    class ListView(MasterDetailCrudPermission.ListView):

        @classmethod
        def get_url_regex(cls):
            return r'^%s$' % cls.model._meta.model_name

        def get_queryset(self):
            qs = super(CrudListView, self).get_queryset()

            perfil = self.perfil()

            kwargs = {self.crud.parent_field: perfil.pk}
            return qs.filter(**kwargs)

        def _as_row(self, obj):
            return [
                (get_field_display(obj, name)[1],
                 self.resolve_url(base.DETAIL, args=(obj.id,))
                 if i == 0 else None)
                for i, name in enumerate(self.list_field_names)]

    class CreateView(MasterDetailCrudPermission.CreateView):

        @classmethod
        def get_url_regex(cls):
            return r'^%s/create$' % cls.model._meta.model_name

        def get_form(self, form_class=None):
            form = super(CrudCreateView,
                         self).get_form(self.form_class)
            field = self.model._meta.get_field(self.crud.parent_field)
            parent = self.perfil()

            setattr(form.instance, self.crud.parent_field, parent)
            return form

    class DeleteView(MasterDetailCrudPermission.DeleteView):

        def get_success_url(self):
            return self.resolve_url(base.LIST)

    class DetailView(MasterDetailCrudPermission.DetailView):

        @classmethod
        def get_url_regex(cls):
            return r'^%s/(?P<pk>\d+)$' % cls.model._meta.model_name

        def get(self, request, *args, **kwargs):
            perfil = self.perfil()

            object = self.model.objects.get(pk=kwargs.get('pk'))

            if object.contato != perfil:
                raise Http404()

            self.object = object

            if hasattr(self.crud, 'model_set') and self.crud.model_set:
                self.object_list = self.get_queryset()
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

        @property
        def detail_list_url(self):
            if self.request.user.has_perm(self.permission(LIST)):
                return self.resolve_url(base.LIST)
            else:
                return ''

        @property
        def detail_create_url(self):
            if self.request.user.has_perm(self.permission(ADD)):
                return self.resolve_url(base.CREATE)
            else:
                return ''

    @classonlymethod
    def get_urls(cls):
        def _add_base(view):
            class CrudViewWithBase(cls.BaseMixin, view):
                model = cls.model
                help_path = cls.help_path
                crud = cls
            CrudViewWithBase.__name__ = view.__name__
            return CrudViewWithBase

        CrudListView = _add_base(cls.ListView)
        CrudCreateView = _add_base(cls.CreateView)
        CrudDetailView = _add_base(cls.DetailView)
        CrudUpdateView = _add_base(cls.UpdateView)
        CrudDeleteView = _add_base(cls.DeleteView)

        return [
            url(regex, view.as_view(), name=view.url_name(suffix))
            for regex, view, suffix in [
                (CrudListView.get_url_regex(),
                 CrudListView, base.LIST),
                (CrudCreateView.get_url_regex(),
                 CrudCreateView, base.CREATE),
                (CrudDetailView.get_url_regex(),
                 CrudDetailView, base.DETAIL),
                (CrudUpdateView.get_url_regex(),
                 CrudUpdateView, base.UPDATE),
                (CrudDeleteView.get_url_regex(),
                 CrudDeleteView, base.DELETE),
            ]]
