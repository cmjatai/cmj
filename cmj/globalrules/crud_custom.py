from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django import forms
from django.conf.urls import url
from django.contrib.auth import logout
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models.base import Model
from django.http.response import Http404
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils import six
from django.utils.datastructures import OrderedSet
from django.utils.decorators import classonlymethod
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import ContextMixin
from django.views.generic.list import MultipleObjectMixin

from cmj.cerimonial.forms import PerfilForm
from cmj.cerimonial.models import Perfil
from cmj.globalrules import (RP_ADD, RP_CHANGE, RP_DELETE, RP_DETAIL, RP_LIST)
from cmj.globalrules import GROUP_SOCIAL_USERS
from cmj.utils import normalize
from sapl.crispy_layout_mixin import get_field_display
from sapl.crud import base
from sapl.crud.base import Crud, CrudListView, CrudCreateView, CrudDetailView,\
    CrudUpdateView, CrudDeleteView, MasterDetailCrud
from sapl.rules import map_rules


class PerfilAbstractCrud(Crud):
    model_set = None
    model = Perfil
    help_path = ''

    class Meta:
        abstract = True

    class BaseMixin(Crud.BaseMixin):

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
            return self.resolve_url(base.ACTION_DETAIL)\
                if self.request.user.has_perm(
                    self.permission(map_rules.RP_ADD)) else ''

        @property
        def update_url(self):
            return self.resolve_url(base.ACTION_UPDATE)\
                if self.request.user.has_perm(
                    self.permission(map_rules.RP_CHANGE)) else ''

        @property
        def delete_url(self):
            return self.resolve_url(base.ACTION_DELETE)\
                if self.request.user.has_perm(
                    self.permission(map_rules.RP_DELETE)) else ''

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['subnav_template_name'] = 'cerimonial/subnav_perfil.yaml'
            return context

    class DetailView(Crud.DetailView):

        def get(self, request, *args, **kwargs):

            try:
                self.object = self.model.objects.for_user(request.user)
            except:
                return redirect(reverse('cmj.cerimonial:perfil_create'))

            return self.render_to_response(self.get_context_data(object=self.object))

    class UpdateView(Crud.UpdateView):

        form_class = PerfilForm
        template_name = 'cerimonial/contato_form.html'

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

            return Crud.UpdateView.post(self, request, *args, **kwargs)

    class DeleteView(Crud.DeleteView):

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

    class CreateView(Crud.CreateView):

        form_class = PerfilForm
        template_name = 'cerimonial/contato_form.html'

        def get(self, request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.contato_set.exists():
                    return redirect(reverse('cmj.cerimonial:perfil_detail'))

            return Crud.CreateView.get(self, request, *args, **kwargs)

        def form_valid(self, form):
            fv = Crud.CreateView.form_valid(self, form)

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
                (CrudListView.get_url_regex(),
                 CrudDetailView, base.ACTION_DETAIL),
                (CrudCreateView.get_url_regex(),
                 CrudCreateView, base.ACTION_CREATE),
                (r'^edit$', CrudUpdateView, base.ACTION_UPDATE),
                (r'^delete$', CrudDeleteView, base.ACTION_DELETE),
            ]]


class PerfilDetailCrudPermission(MasterDetailCrud):

    class BaseMixin(MasterDetailCrud.BaseMixin):

        def perfil(self):
            try:
                perfil = Perfil.objects.for_user(self.request.user)
            except:
                return redirect(reverse('cmj.cerimonial:perfil_create'))
            return perfil

        @property
        def list_url(self):
            return self.resolve_url(base.ACTION_LIST)\
                if self.request.user.has_perm(self.permission(RP_LIST)) else ''

        @property
        def create_url(self):
            return self.resolve_url(base.ACTION_CREATE)\
                if self.request.user.has_perm(self.permission(RP_ADD)) else ''

        @property
        def detail_url(self):
            return self.resolve_url(
                base.ACTION_DETAIL, args=(self.object.id,))\
                if self.request.user.has_perm(self.permission(RP_DETAIL)) else ''

        @property
        def update_url(self):
            return self.resolve_url(
                base.ACTION_UPDATE, args=(self.object.id,))\
                if self.request.user.has_perm(self.permission(RP_CHANGE)) else ''

        @property
        def delete_url(self):
            return self.resolve_url(
                base.ACTION_DELETE, args=(self.object.id,))\
                if self.request.user.has_perm(self.permission(RP_DELETE)) else ''

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

    class ListView(MasterDetailCrud.ListView):

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

    class CreateView(MasterDetailCrud.CreateView):

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

    class DeleteView(MasterDetailCrud.DeleteView):

        def get_success_url(self):
            return self.resolve_url(base.LIST)

    class DetailView(MasterDetailCrud.DetailView):

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
            if self.request.user.has_perm(self.permission(map_rules.RP_LIST)):
                return self.resolve_url(base.ACTION_LIST)
            else:
                return ''

        @property
        def detail_create_url(self):
            if self.request.user.has_perm(self.permission(map_rules.RP_ADD)):
                return self.resolve_url(base.ACTION_CREATE)
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
                 CrudListView, base.ACTION_LIST),
                (CrudCreateView.get_url_regex(),
                 CrudCreateView, base.ACTION_CREATE),
                (CrudDetailView.get_url_regex(),
                 CrudDetailView, base.ACTION_DETAIL),
                (CrudUpdateView.get_url_regex(),
                 CrudUpdateView, base.ACTION_UPDATE),
                (CrudDeleteView.get_url_regex(),
                 CrudDeleteView, base.ACTION_DELETE),
            ]]
