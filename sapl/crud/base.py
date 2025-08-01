from abc import ABC
import logging

from braces.views import FormMessagesMixin
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from crispy_forms.layout import Field, Layout
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.http.response import Http404
from django.shortcuts import redirect
from django.urls.base import reverse
from django.urls.conf import re_path
from django.utils.decorators import classonlymethod
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.views.generic.base import ContextMixin
from django.views.generic.list import MultipleObjectMixin

from sapl.crispy_layout_mixin import CrispyLayoutFormMixin, get_field_display
from sapl.crispy_layout_mixin import SaplFormHelper
from sapl.rules import (RP_ADD, RP_CHANGE, RP_DELETE, RP_DETAIL,
                        RP_LIST)
from sapl.utils import normalize


logger = logging.getLogger(settings.BASE_DIR.name)


ACTION_LIST, ACTION_CREATE, ACTION_DETAIL, ACTION_UPDATE, ACTION_DELETE = \
    'list', 'create', 'detail', 'update', 'delete'


def _form_invalid_message(msg):
    return '%s %s' % (_('Formulário inválido.'), msg)


FORM_MESSAGES = {ACTION_CREATE: (_('Registro criado com sucesso!'),
                                 _('O registro não foi criado.')),
                 ACTION_UPDATE: (_('Registro alterado com sucesso!'),
                                 _('Suas alterações não foram salvas.')),
                 ACTION_DELETE: (_('Registro excluído com sucesso!'),
                                 _('O registro não foi excluído.'))}
FORM_MESSAGES = {k: (a, _form_invalid_message(b))
                 for k, (a, b) in FORM_MESSAGES.items()}


def from_to(start, end):
    return list(range(start, end + 1))


def make_pagination(index, num_pages):
    '''Make a list of adjacent page ranges interspersed with "None"s

    The list starts with [1, 2] and end with [num_pages-1, num_pages].
    The list includes [index-1, index, index+1]
    "None"s separate those ranges and mean ellipsis (...)

    Example:  [1, 2, None, 10, 11, 12, None, 29, 30]
    '''

    PAGINATION_LENGTH = 10
    if num_pages <= PAGINATION_LENGTH:
        return from_to(1, num_pages)
    else:
        if index - 1 <= 5:
            tail = [num_pages - 1, num_pages]
            head = from_to(1, PAGINATION_LENGTH - 3)
        else:
            if index + 1 >= num_pages - 3:
                tail = from_to(index - 1, num_pages)
            else:
                tail = [index - 1, index, index + 1,
                        None, num_pages - 1, num_pages]
            head = from_to(1, PAGINATION_LENGTH - len(tail) - 1)
        return head + [None] + tail


"""
variáveis do crud:
    help_topic
    container_field
    container_field_set
    is_m2m
    model
    model_set
    form_search_class -> depende de o model relativo implementar SearchMixin
    list_field_names
    list_field_names_set -> lista reversa em details
    permission_required -> este atributo ser vazio não nulo torna a view publ
    layout_key_set
    layout_key
    ordered_list = False desativa os clicks e controles de ord da listagem
    parent_field = parentesco reverso separado por '__'
    namespace
    return_parent_field_url
"""


class SearchMixin(models.Model):

    search = models.TextField(blank=True, default='')
    logger = logging.getLogger(__name__)

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, auto_update_search=True):

        if auto_update_search and hasattr(self, 'fields_search'):
            search = ''
            for str_field in self.fields_search:
                fields = str_field.split('__')
                if len(fields) == 1:
                    try:
                        search += str(getattr(self, str_field)) + ' '
                    except Exception as e:
                        username = self.request.user.username
                        self.logger.error("user=" + username + ". " + str(e))
                else:
                    _self = self
                    for field in fields:
                        _self = getattr(_self, field)
                    search += str(_self) + ' '
            self.search = search
        self.search = normalize(self.search)

        return super(SearchMixin, self).save(
            force_insert=force_insert, force_update=force_update,
            using=using, update_fields=update_fields)


class ListWithSearchForm(forms.Form):
    q = forms.CharField(required=False, label='',
                        widget=forms.TextInput(
                            attrs={'type': 'search'}))

    o = forms.CharField(required=False, label='',
                        widget=forms.HiddenInput())

    class Meta:
        fields = ['q', 'o']

    def __init__(self, *args, **kwargs):
        super(ListWithSearchForm, self).__init__(*args, **kwargs)

        self.helper = SaplFormHelper()
        self.form_class = 'form-inline'
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Field('o'),
            FieldWithButtons(
                Field('q',
                      placeholder=_('Filtrar Lista'),
                      css_class='input-lg'),
                StrictButton(
                    _('Filtrar'), css_class='btn-outline-primary btn-lg',
                    type='submit'))
        )


class PermissionRequiredForAppCrudMixin(PermissionRequiredMixin):

    def has_permission(self):
        apps = self.app_label
        if isinstance(apps, str):
            apps = apps,
        # app_label vazio dará acesso geral
        for app in apps:
            if not self.request.user.has_module_perms(app):
                return False
        return True


class PermissionRequiredContainerCrudMixin(PermissionRequiredMixin):

    def has_permission(self):
        perms = self.get_permission_required()

        # Torna a view pública se não possuir conteudo
        # no atributo permission_required

        if not len(perms):
            return True

        for perm in perms:
            if self.request.user.has_perm(perm):
                return True
        return False

        # return self.request.user.has_perms(perms) if len(perms) else True

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()

        if 'pk' in kwargs:
            params = {'pk': kwargs['pk']}

            if self.container_field:
                params[self.container_field] = request.user.pk

                if not self.model.objects.filter(**params).exists():
                    raise Http404()

        elif self.container_field:
            container = self.container_field.split('__')

            if len(container) > 1:
                container_model = getattr(
                    self.model, container[0]).field.related_model

                params = {}
                params['__'.join(
                    container[1:])] = request.user.pk

                if not container_model.objects.filter(**params).exists():
                    messages.error(
                        request,
                        'O Usuário (%s) não está registrado como (%s).' % (
                            request.user, container_model._meta.verbose_name))
                    return redirect('/')
            else:
                # TODO: implementar caso o user for o próprio o container
                pass

        return super(PermissionRequiredMixin, self).dispatch(
            request, *args, **kwargs)

    @property
    def container_field(self):
        if hasattr(self, 'crud') and not hasattr(self.crud, 'container_field'):
            self.crud.container_field = ''
        if hasattr(self, 'crud'):
            return self.crud.container_field

    @property
    def container_field_set(self):
        if hasattr(self, 'crud') and\
                not hasattr(self.crud, 'container_field_set'):
            self.crud.container_field_set = ''
        if hasattr(self, 'crud'):
            return self.crud.container_field_set

    @property
    def is_contained(self):
        return self.container_field_set or self.container_field


class CrudBaseMixin(CrispyLayoutFormMixin):

    def __init__(self, **kwargs):
        super(CrudBaseMixin, self).__init__(**kwargs)
        obj = self.crud if hasattr(self, 'crud') else self
        self.app_label = obj.model._meta.app_label
        self.model_name = obj.model._meta.model_name

        if hasattr(obj, 'model_set') and obj.model_set:
            self.app_label_set = getattr(
                obj.model, obj.model_set).field.model._meta.app_label
            self.model_name_set = getattr(
                obj.model, obj.model_set).field.model._meta.model_name

        if not hasattr(obj, 'public'):
            obj.public = []

        if hasattr(self, 'permission_required') and self.permission_required:

            self.permission_required = tuple(
                (
                    self.permission(pr) for pr in (
                        set(self.permission_required) - set(obj.public)
                    )
                )
            )

    @classmethod
    def url_name(cls, suffix):
        return '%s_%s' % (cls.model._meta.model_name, suffix)

    def url_name_set(self, suffix):
        obj = self.crud if hasattr(self, 'crud') else self
        return '%s_%s' % (getattr(obj.model, obj.model_set
                                  ).field.model._meta.model_name, suffix)

    def permission(self, rad):
        return '%s%s%s' % (self.app_label if rad.endswith('_') else '',
                           rad,
                           self.model_name if rad.endswith('_') else '')

    def permission_set(self, rad):
        return '%s%s%s' % (self.app_label_set if rad.endswith('_') else '',
                           rad,
                           self.model_name_set if rad.endswith('_') else '')

    def resolve_url(self, suffix, args=None):
        namespace = self.model._meta.app_config.name
        return reverse('%s:%s' % (namespace, self.url_name(suffix)),
                       args=args)

    def resolve_url_set(self, suffix, args=None):
        obj = self.crud if hasattr(self, 'crud') else self
        namespace = getattr(
            obj.model, obj.model_set).field.model._meta.app_config.name
        return reverse('%s:%s' % (namespace, self.url_name_set(suffix)),
                       args=args)

    @property
    def ordered_list(self):
        return True

    @property
    def list_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.ListView:
            return ''
        if not obj.ListView.permission_required:
            return self.resolve_url(ACTION_LIST)
        else:
            return self.resolve_url(
                ACTION_LIST) if self.request.user.has_perm(
                self.permission(RP_LIST)) else ''

    @property
    def create_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.CreateView:
            return ''
        if not obj.CreateView.permission_required:
            return self.resolve_url(ACTION_CREATE)
        else:
            return self.resolve_url(
                ACTION_CREATE) if self.request.user.has_perm(
                self.permission(RP_ADD)) else ''

    @property
    def detail_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.DetailView:
            return ''
        if not obj.DetailView.permission_required:
            return self.resolve_url(ACTION_DETAIL, args=(self.object.id,))
        else:
            return self.resolve_url(ACTION_DETAIL, args=(self.object.id,))\
                if self.request.user.has_perm(
                    self.permission(RP_DETAIL)) else ''

    @property
    def update_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.UpdateView:
            return ''
        if not obj.UpdateView.permission_required:
            return self.resolve_url(ACTION_UPDATE, args=(self.object.id,))
        else:
            return self.resolve_url(ACTION_UPDATE, args=(self.object.id,))\
                if self.request.user.has_perm(
                    self.permission(RP_CHANGE)) else ''

    @property
    def delete_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if not obj.DeleteView:
            return ''
        if not obj.DeleteView.permission_required:
            return self.resolve_url(ACTION_DELETE, args=(self.object.id,))
        else:
            return self.resolve_url(ACTION_DELETE, args=(self.object.id,))\
                if self.request.user.has_perm(
                    self.permission(RP_DELETE)) else ''

    @property
    def openapi_url(self):
        obj = self.crud if hasattr(self, 'crud') else self
        o = self.object
        url = f'/api/{o._meta.app_label}/{o._meta.model_name}/{o.id}'
        return url

    def get_template_names(self):
        names = super(CrudBaseMixin, self).get_template_names()
        names.append("crud/%s.html" %
                     self.template_name_suffix.lstrip('_'))
        return names

    @property
    def verbose_name_set(self):
        obj = self.crud if hasattr(self, 'crud') else self
        return getattr(obj.model, obj.model_set).field.model._meta.verbose_name

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural


class CrudListView(PermissionRequiredContainerCrudMixin, ListView):
    permission_required = (RP_LIST, )
    logger = logging.getLogger(__name__)
    paginate_by = 10
    no_entries_msg = _('Nenhum registro encontrado.')

    @classmethod
    def get_url_regex(cls):
        return r'^$'

    def get_rows(self, object_list):
        return [self._as_row(obj) for obj in object_list]

    def get_headers(self):
        """
        Transforma o headers de fields de list_field_names
        para junção de fields via tuplas.
        list_field_names pode ser construido como
        list_field_names=('nome', 'endereco', ('telefone', sexo'), 'dat_nasc')
        ou ainda:
          list_field_names = ['composicao__comissao__nome', 'cargo__nome', (
          'composicao__periodo__data_inicio', 'composicao__periodo__data_fim')]
        """
        r = []
        for fieldname in self.list_field_names:
            if not isinstance(fieldname, tuple):
                fieldname = fieldname,
            s = []
            for fn in fieldname:
                m = self.model
                fn = fn.split('__')
                for f in fn:
                    if not f:
                        continue
                    try:
                        f = m._meta.get_field(f)
                        if hasattr(f, 'related_model') and f.related_model:
                            m = f.related_model
                    except:
                        pass
                if f:
                    hook = 'hook_header_{}'.format(''.join(fn))
                    if hasattr(self, hook):
                        header = getattr(self, hook)()
                        s.append(force_str(header))
                    else:
                        s.append(force_str(f.verbose_name))
                else:
                    hook = 'hook_header_{}'.format(''.join(fn))
                    if hasattr(self, hook):
                        header = getattr(self, hook)()
                        s.append(header)

            s = ' / '.join(filter(lambda x: x, s))
            r.append(s)
        return r

    def _as_row(self, obj):
        r = []
        for i, name in enumerate(self.list_field_names):
            url = self.resolve_url(
                ACTION_DETAIL, args=(obj.id,)) if i == 0 else None

            """Caso o crud list seja para uma relação ManyToManyField"""
            if url and hasattr(self, 'crud') and\
                    hasattr(self.crud, 'is_m2m') and self.crud.is_m2m:
                url = url + ('?pkk=' + self.kwargs['pk']
                             if 'pk' in self.kwargs else '')

            if not isinstance(name, tuple):
                name = name,

            """ se elemento de list_field_name for uma tupla, constrói a
            informação com ' / ' se os campos forem simples,
            ou com <br> se for m2m """
            if isinstance(name, tuple):
                s = ''
                for j, n in enumerate(name):
                    if not n:
                        s += '<br>'
                        continue

                    m = obj
                    n = n.split('__')
                    for f in n[:-1]:
                        m = getattr(m, f)
                        if not m:
                            break

                    ss = ''
                    try:
                        if m:
                            ss = get_field_display(m, n[-1])[1]
                            ss = (
                                ('<br>' if '<ul>' in ss else ' / ') + ss)\
                                if ss and j != 0 and s else ss
                    except:
                        pass
                    finally:
                        hook = 'hook_{}'.format(''.join(n))
                        if hasattr(self, hook):
                            hs, url = getattr(self, hook)(obj, ss, url)
                            s += str(hs)
                        else:
                            s += ss

                r.append((s, url))
        return r

    def get_context_data(self, **kwargs):
        """ Relevante se na implmentação do crud list, for informado
        um formulário de pesquisa herdado ou o próprio ListWithSearchForm.
        Só pode ser usado se o model relativo herdar de SearchMixin"""
        if hasattr(self, 'form_search_class'):
            q = str(self.request.GET.get('q'))\
                if 'q' in self.request.GET else ''

            o = self.request.GET['o'] if 'o' in self.request.GET else '1'

            if 'form' not in kwargs:
                initial = self.get_initial() if hasattr(
                    self, 'get_initial') else {}
                initial.update({'q': q, 'o': o})
                kwargs['form'] = self.form_search_class(
                    initial=initial)

        count = self.object_list.count()
        context = super().get_context_data(**kwargs)
        context.setdefault('title', self.verbose_name_plural)
        context['count'] = count

        # pagination
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

        qr = self.request.GET.copy()
        if 'page' in qr:
            del qr['page']
        context['filter_url'] = (
            '&' + qr.urlencode()) if len(qr) > 0 else ''

        if self.ordered_list:
            if 'o' in qr:
                del qr['o']
            context['ordering_url'] = (
                '&' + qr.urlencode()) if len(qr) > 0 else ''
        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        # form_search_class
        # só pode ser usado em models que herdam de SearchMixin
        if hasattr(self, 'form_search_class'):
            request = self.request
            if request.GET.get('q') is not None:
                query = normalize(str(request.GET.get('q')))

                query = query.split(' ')
                if query:
                    q = models.Q()
                    for item in query:
                        if not item:
                            continue
                        q = q & models.Q(search__icontains=item)

                    if q:
                        queryset = queryset.filter(q)

        if self.ordered_list:
            list_field_names = self.list_field_names
            o = '1'
            desc = ''
            if 'o' in self.request.GET:
                o = self.request.GET['o']
                desc = '-' if o.startswith('-') else ''

                # Constroi a ordenação da listagem com base no que o usuário
                # clicar
                try:
                    fields_for_ordering = list_field_names[
                        (abs(int(o)) - 1) % len(list_field_names)]

                    if isinstance(fields_for_ordering, str):
                        fields_for_ordering = [fields_for_ordering, ]

                    ordering = ()
                    model = self.model
                    for fo in fields_for_ordering:
                        if not fo:
                            continue

                        fm = None
                        if '__' not in fo:
                            try:
                                fm = model._meta.get_field(fo)
                            except Exception as e:
                                username = self.request.user.username
                                self.logger.error(
                                    "user=" + username + ". " + str(e))
                                pass

                            if fm and hasattr(fm, 'related_model')\
                                    and fm.related_model:
                                rmo = fm.related_model._meta.ordering
                                if rmo:
                                    rmo = rmo[0]
                                    if not isinstance(rmo, str):
                                        rmo = rmo[0]
                                    if rmo.startswith('-'):
                                        rmo = rmo[1:]
                                    fo = '%s__%s' % (fo, rmo)
                        else:
                            fo = desc + fo
                            ordering += (fo,)

                        if fm:
                            fo = desc + fo
                            ordering += (fo,)

                    model = self.model
                    model_ordering = model._meta.ordering
                    if model_ordering:
                        if isinstance(model_ordering, str):
                            model_ordering = (model_ordering,)
                        for mo in model_ordering:
                            if mo not in ordering:
                                ordering = ordering + (mo, )

                    queryset = queryset.order_by(*ordering)

                    # print(ordering)
                except Exception as e:
                    logger.error(self.request)
                    logger.error(format_lazy(
                        '{} {}',
                        _('ERRO: construção da tupla de ordenação.'),
                        str(e)))

        # print(queryset.query)
        if not self.request.user.is_authenticated:
            return queryset

        if self.container_field:
            params = {}
            params[self.container_field] = self.request.user.pk
            queryset = queryset.filter(**params)

        return queryset


class CrudCreateView(PermissionRequiredContainerCrudMixin,
                     FormMessagesMixin, CreateView):
    permission_required = (RP_ADD, )
    logger = logging.getLogger(__name__)

    @classmethod
    def get_url_regex(cls):
        return r'^/create$'

    form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_CREATE]

    @property
    def cancel_url(self):

        if hasattr(super(), 'cancel_url'):
            return super().cancel_url

        return self.list_url

    def get_success_url(self):
        return self.detail_url

    def get_context_data(self, **kwargs):
        kwargs.setdefault('title', _('Adicionar %(verbose_name)s') % {
            'verbose_name': self.verbose_name})
        return super(CrudCreateView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        self.object = form.instance
        try:
            self.object.owner = self.request.user
            self.object.modifier = self.request.user
        except Exception as e:
            username = self.request.user.username
            self.logger.error("user=" + username + ". " + str(e))
            pass

        if self.container_field:
            container = self.container_field.split('__')

            if len(container) > 1:
                # TODO: implementar caso o user for próprio o container
                container_model = getattr(
                    self.model, container[0]).field.related_model

                params = {}
                params['__'.join(
                    container[1:])] = self.request.user.pk

                if 'pk' in self.kwargs:
                    params['pk'] = self.kwargs['pk']

                container_data = container_model.objects.filter(
                    **params).first()

                if not container_data:
                    raise Exception(
                        _('Não é permitido adicionar um registro '
                          'sem estar em um Container %s'
                          ) % container_model._meta.verbose_name)

                if hasattr(self, 'crud') and\
                        hasattr(self.crud, 'is_m2m') and self.crud.is_m2m:
                    setattr(
                        self.object, container[1], getattr(
                            container_data, container[1]))
                    response = super().form_valid(form)
                    getattr(self.object, container[0]).add(container_data)
                    return response
                else:
                    setattr(self.object, container[0], container_data)

        return super().form_valid(form)


class CrudDetailView(PermissionRequiredContainerCrudMixin,
                     DetailView, MultipleObjectMixin):

    permission_required = (RP_DETAIL, )
    no_entries_msg = _('Nenhum registro Associado.')
    paginate_by = 10
    logger = logging.getLogger(__name__)

    @classmethod
    def get_url_regex(cls):
        return r'^/(?P<pk>\d+)$'

    def get_rows(self, object_list):
        return [self._as_row(obj) for obj in object_list]

    def get_headers(self):
        if not self.object_list:
            return []
        try:
            obj = self.crud if hasattr(self, 'crud') else self
            """return [
                (getattr(
                    self.object, obj.model_set).model._meta.get_field(
                    fieldname).verbose_name
                 if hasattr(self.object, fieldname) else
                    getattr(
                    self.object, obj.model_set).model._meta.get_field(
                    fieldname).related_model._meta.verbose_name_plural)
                for fieldname in self.list_field_names_set]"""

            r = []
            list_field_names_set = self.list_field_names_set or []
            for fieldname in list_field_names_set:

                if hasattr(self.object, fieldname):
                    fv = getattr(
                        self.object, obj.model_set).model._meta.get_field(
                        fieldname).verbose_name
                else:
                    try:
                        fv = getattr(self.object, obj.model_set).model._meta.get_field(
                            fieldname)
                    except:
                        fv = ''
                    if hasattr(fv, 'related_model') and fv.related_model:
                        fv = fv.related_model._meta.verbose_name_plural
                    elif hasattr(fv, 'verbose_name') and fv.verbose_name:
                        fv = fv.verbose_name
                    else:
                        hook = f'hook_header_{fieldname}'
                        if hasattr(self, hook):
                            fv = getattr(self, hook)()

                r.append(fv)

            return r

        except Exception as e:
            username = self.request.user.username
            self.logger.error("user=" + username + ". " + str(e))
            obj = self.crud if hasattr(self, 'crud') else self
            return [getattr(
                self.object,
                obj.model_set).model._meta.verbose_name_plural]

    def url_model_set_name(self, suffix):
        return '%s_%s' % (
            getattr(self.object,
                    self.crud.model_set).model._meta.model_name,
            suffix)

    def resolve_model_set_url(self, suffix, args=None):
        obj = self.crud if hasattr(self, 'crud') else self
        namespace = getattr(
            self.object, obj.model_set).model._meta.app_config.name
        return reverse('%s:%s' % (
            namespace, self.url_model_set_name(suffix)),
            args=args)

    def _as_row(self, obj):
        try:
            try:
                r = []
                for i, name in enumerate(self.list_field_names_set):
                    c = self.get_column(name, '', obj=obj).get('text', '')
                    r.append(
                        (
                            c,
                            self.resolve_model_set_url(ACTION_DETAIL, args=(obj.id,)) if not i else None
                        )
                    )
                return r
            except Exception as e:
                return [(
                    get_field_display(obj, name)[1],
                    self.resolve_model_set_url(ACTION_DETAIL, args=(obj.id,))
                    if i == 0 else None)
                    for i, name in enumerate(self.list_field_names_set)]
        except Exception as e:
            username = self.request.user.username
            self.logger.error("user=" + username + ". " + str(e))
            return [(
                getattr(obj, name),
                self.resolve_model_set_url(ACTION_DETAIL, args=(obj.id,))
                if i == 0 else None)
                for i, name in enumerate(self.list_field_names_set)]

    def get_object(self, queryset=None):
        if hasattr(self, 'object'):
            return self.object
        return DetailView.get_object(self, queryset=queryset)

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.model.objects.get(pk=kwargs['pk'])
        except Exception as e:
            username = request.user.username
            self.logger.error("user=" + username + ". " + str(e))
            raise Http404
        obj = self.crud if hasattr(self, 'crud') else self
        if hasattr(obj, 'model_set') and obj.model_set:
            self.object_list = self.get_queryset()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        obj = self.crud if hasattr(self, 'crud') else self
        if hasattr(obj, 'model_set') and obj.model_set:
            queryset = getattr(self.object, obj.model_set).all()
        else:
            queryset = super().get_queryset()

        if not self.request.user.is_authenticated:
            return queryset

        if self.container_field_set:
            params = {}
            params[self.container_field_set] = self.request.user.pk
            return queryset.filter(**params)

        return queryset

    def get_context_data(self, **kwargs):
        obj = self.crud if hasattr(self, 'crud') else self
        if hasattr(obj, 'model_set') and obj.model_set:
            count = self.object_list.count()
            context = MultipleObjectMixin.get_context_data(self, **kwargs)
            context['count'] = count
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

    @property
    def model_set_verbose_name(self):
        obj = self.crud if hasattr(self, 'crud') else self
        return getattr(
            self.object,
            obj.model_set).model._meta.verbose_name

    @property
    def model_set_verbose_name_plural(self):
        obj = self.crud if hasattr(self, 'crud') else self
        return getattr(
            self.object,
            obj.model_set).model._meta.verbose_name_plural


class CrudUpdateView(PermissionRequiredContainerCrudMixin,
                     FormMessagesMixin, UpdateView):
    permission_required = (RP_CHANGE, )
    logger = logging.getLogger(__name__)

    def form_valid(self, form):

        self.object = form.instance
        try:
            self.object.modifier = self.request.user
        except Exception as e:
            username = self.request.user.username
            self.logger.error("user=" + username + ". " + str(e))
            pass

        return super().form_valid(form)

    @classmethod
    def get_url_regex(cls):
        return r'^/(?P<pk>\d+)/edit$'

    form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_UPDATE]

    @property
    def cancel_url(self):
        return self.detail_url

    def get_success_url(self):
        return self.detail_url


class CrudDeleteView(PermissionRequiredContainerCrudMixin,
                     FormMessagesMixin, DeleteView):
    permission_required = (RP_DELETE, )
    logger = logging.getLogger(__name__)

    @classmethod
    def get_url_regex(cls):
        return r'^/(?P<pk>\d+)/delete$'

    form_valid_message, form_invalid_message = FORM_MESSAGES[ACTION_DELETE]

    @property
    def cancel_url(self):
        return self.detail_url

    def get_success_url(self):
        return self.list_url

    def delete(self, request, *args, **kwargs):
        try:
            return super(CrudDeleteView, self).delete(request, args, kwargs)
        except models.ProtectedError as err:
            error_msg = 'Registro não pode ser removido, pois\
                         é referenciado por outros registros:<br>\
                         <ul>'
            error_msg2 = ''
            for i in err.protected_objects:
                error_msg += '<li>{} - {}</li>'.format(
                    i._meta.verbose_name, i
                )
                error_msg2 += '{} - {}, '.format(
                    i._meta.verbose_name, i
                )
            error_msg2 = error_msg2[:len(error_msg2) - 2] + '.'
            error_msg += '</ul>'

            username = request.user.username
            self.logger.error("user=" + username + ". Registro não pode ser removido, pois "
                              "é referenciado por outros registros: " + error_msg2)
            messages.add_message(request,
                                 messages.ERROR,
                                 error_msg)
            return self.render_to_response(self.get_context_data())


class Crud:
    __type__ = True

    BaseMixin = CrudBaseMixin
    ListView = CrudListView
    CreateView = CrudCreateView
    DetailView = CrudDetailView
    UpdateView = CrudUpdateView
    DeleteView = CrudDeleteView
    help_topic = ''
    frontend = ''

    class PublicMixin:
        permission_required = []

    @classonlymethod
    def get_urls(cls):

        def _add_base(view):

            if not view:
                return

            if not cls.__type__:
                return view

            pr = set(view.permission_required) if hasattr(
                view, 'permission_required') else set()

            if hasattr(view, 'permission_required') and \
                    view.permission_required and \
                    hasattr(cls, 'public') and \
                    cls.public:

                #print(view.permission_required, view)
                #print(cls.public, cls)

                pr = pr - set(cls.public)

            class CrudViewWithBase(cls.BaseMixin, view):
                permission_required = tuple(pr)
                model = cls.model
                help_topic = cls.help_topic
                crud = cls

            CrudViewWithBase.__name__ = view.__name__
            return CrudViewWithBase

        # if 'EmendaLoaCrud' in str(cls):
        #    print('EmendaLoaCrud')

        CrudListView = _add_base(cls.ListView)
        CrudCreateView = _add_base(cls.CreateView)
        CrudDetailView = _add_base(cls.DetailView)
        CrudUpdateView = _add_base(cls.UpdateView)
        CrudDeleteView = _add_base(cls.DeleteView)

        cruds = CrudListView, CrudCreateView, CrudDetailView, CrudUpdateView, CrudDeleteView

        if cls.__type__:
            class CRUD(cls):
                __type__ = False
                ListView = CrudListView
                CreateView = CrudCreateView
                DetailView = CrudDetailView
                UpdateView = CrudUpdateView
                DeleteView = CrudDeleteView

            for c in cruds:
                if c:
                    c.crud = CRUD

        cruds_base = [
            [CrudListView.get_url_regex()
             if CrudListView else None, CrudListView, ACTION_LIST],
            [CrudCreateView.get_url_regex()
             if CrudCreateView else None, CrudCreateView, ACTION_CREATE],
            [CrudDetailView.get_url_regex()
             if CrudDetailView else None, CrudDetailView, ACTION_DETAIL],
            [CrudUpdateView.get_url_regex()
             if CrudUpdateView else None, CrudUpdateView, ACTION_UPDATE],
            [CrudDeleteView.get_url_regex()
             if CrudDeleteView else None, CrudDeleteView, ACTION_DELETE]]

        cruds = []
        for crud in cruds_base:
            if crud[0]:
                cruds.append(crud)
                if not isinstance(crud[0], tuple):
                    crud[0] = ((crud[0], ''), )

        urls = []
        for regex_list, view, suffix in cruds:
            for regex, suf in regex_list:
                suf = f'{suffix}_{suf}' if suf else suffix
                u = re_path(regex, view.as_view(),
                            name=view.url_name(suf))
                urls.append(u)

        return urls

    @classonlymethod
    def build(cls, _model, _help_topic, _model_set=None, list_field_names=[]):

        def create_class(_list_field_names):
            class ModelCrud(cls):
                model = _model
                model_set = _model_set
                help_topic = _help_topic
                list_field_names = _list_field_names
            return ModelCrud

        ModelCrud = create_class(list_field_names)
        ModelCrud.__name__ = '%sCrud' % _model.__name__
        return ModelCrud


class CrudAux(Crud):
    """
        Checa permissão para ver qualquer dado de tabela auxiliar
        a permissão base.view_tabelas_auxiliares está definada class Meta
        do model sapl.base.models.AppConfig que, naturalmente é um arquivo
        de configuração geral e só pode ser acessado através das Tabelas
        Auxiliares... Com isso o script de geração de perfis acaba que por
        criar essa permissão apenas para o perfil Operador Geral.
    """
    permission_required = ('base.view_tabelas_auxiliares',)

    class ListView(Crud.ListView):
        template_name = "crud/list_tabaux.html"

    class BaseMixin(Crud.BaseMixin):
        subnav_template_name = None

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            """Força o template filter subnav em base/templatetags/menus.py
            a abrir um yaml diferente do padrão.
            Se o valor de subnav_template_name é nulo faz o filter subnav
            não abrir o padrão e nem um outro arquivo.
            """
            if 'subnav_template_name' not in context:
                context['subnav_template_name'] = self.subnav_template_name
            return context

    @classonlymethod
    def build(cls, _model, _help_topic, _model_set=None, list_field_names=[]):

        ModelCrud = Crud.build(
            _model, _help_topic, _model_set, list_field_names)

        class ModelCrudAux(CrudAux, ModelCrud):
            pass

        return ModelCrudAux


class MasterDetailCrud(Crud):
    is_m2m = False
    link_return_to_parent_field = False

    class BaseMixin(Crud.BaseMixin):

        @property
        def list_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.ListView:
                return ''
            return self.resolve_url(ACTION_LIST, args=(self.kwargs['pk'],))\
                if self.request.user.has_perm(self.permission(RP_LIST)) else ''

        @property
        def create_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.CreateView:
                return ''
            return self.resolve_url(ACTION_CREATE, args=(self.kwargs['pk'],))\
                if self.request.user.has_perm(self.permission(RP_ADD)) else ''

        @property
        def detail_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.DetailView:
                return ''
            pkk = self.request.GET['pkk'] if 'pkk' in self.request.GET else ''
            return (super().detail_url + (('?pkk=' + pkk) if pkk else ''))\
                if self.request.user.has_perm(
                    self.permission(RP_DETAIL)) else ''

        @property
        def update_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.UpdateView:
                return ''
            pkk = self.request.GET['pkk'] if 'pkk' in self.request.GET else ''
            return (super().update_url + (('?pkk=' + pkk) if pkk else ''))\
                if self.request.user.has_perm(
                    self.permission(RP_CHANGE)) else ''

        @property
        def delete_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.DeleteView:
                return ''
            return super().delete_url\
                if self.request.user.has_perm(
                    self.permission(RP_DELETE)) else ''

        def get_context_data(self, **kwargs):
            obj = self.crud if hasattr(self, 'crud') else self
            self.object = getattr(self, 'object', None)
            parent_object = None
            if self.object:
                if '__' in obj.parent_field:
                    fields = obj.parent_field.split('__')
                    parent_object = self.object
                    for field in fields:
                        parent_object = getattr(parent_object, field)
                else:
                    parent_object = getattr(self.object, obj.parent_field)

                if not isinstance(parent_object, models.Model):
                    if parent_object.count() > 1:
                        if 'pkk' not in self.request.GET:
                            raise Http404()
                        root_pk = self.request.GET['pkk']
                        parent_object = parent_object.filter(id=root_pk)

                    parent_object = parent_object.first()

                    if not parent_object:
                        raise Http404()

                root_pk = parent_object.pk
            else:
                root_pk = self.kwargs['pk'] if 'pkk' not in self.request.GET\
                    else self.request.GET['pkk']
            kwargs.setdefault('root_pk', root_pk)
            context = super(CrudBaseMixin, self).get_context_data(**kwargs)

            if parent_object:
                context['title'] = '%s <small>(%s)</small>' % (
                    self.object, parent_object)

            return context

    class ListView(Crud.ListView):
        permission_required = RP_LIST,
        logger = logging.getLogger(__name__)

        def get(self, request, *args, **kwargs):
            return Crud.ListView.get(self, request, *args, **kwargs)

        @classmethod
        def get_url_regex(cls):
            return r'^/(?P<pk>\d+)/%s$' % cls.model._meta.model_name

        def get_context_data(self, **kwargs):
            obj = self.crud if hasattr(self, 'crud') else self
            context = CrudListView.get_context_data(self, **kwargs)

            parent_model = None
            if '__' in obj.parent_field:
                fields = obj.parent_field.split('__')
                parent_model = pm = self.model
                for field in fields:
                    pm = getattr(pm, field)
                    if isinstance(pm.field, ForeignKey):
                        parent_model = getattr(
                            parent_model, field).field.related_model
                    else:
                        parent_model = getattr(
                            parent_model, field).rel.related_model
                    pm = parent_model

            else:
                parent_model = getattr(
                    self.model, obj.parent_field)
                if isinstance(parent_model.field, (
                        ForeignKey, ManyToManyField)):
                    parent_model = parent_model.field.related_model
                else:
                    parent_model = parent_model.rel.related_model

            params = {'pk': kwargs['root_pk']}

            if self.container_field:
                container = self.container_field.split('__')
                if len(container) > 1:
                    params['__'.join(container[1:])] = self.request.user.pk

            try:
                self.parent_object = parent_model.objects.get(**params)
            except Exception as e:
                username = self.request.user.username
                self.logger.error("user=" + username + ". " + str(e))
                raise Http404()

            context[
                'title'] = '%s <small>(%s)</small>' % (
                context['title'], self.parent_object)
            return context

        def get_queryset(self):
            obj = self.crud if hasattr(self, 'crud') else self
            qs = super().get_queryset()

            kwargs = {obj.parent_field: self.kwargs['pk']}

            """if self.container_field:
                kwargs[self.container_field] = self.request.user.pk"""

            return qs.filter(**kwargs)

        def dispatch(self, request, *args, **kwargs):
            return PermissionRequiredMixin.dispatch(self, request, *args, **kwargs)

    class CreateView(Crud.CreateView):
        permission_required = RP_ADD,
        logger = logging.getLogger(__name__)

        def dispatch(self, request, *args, **kwargs):
            return PermissionRequiredMixin.dispatch(
                self, request, *args, **kwargs)

        @classmethod
        def get_url_regex(cls):
            return r'^/(?P<pk>\d+)/%s/create$' % cls.model._meta.model_name

        def get_form(self, form_class=None):
            obj = self.crud if hasattr(self, 'crud') else self
            form = super(MasterDetailCrud.CreateView, self).get_form(
                self.form_class)
            parent_field = obj.parent_field.split('__')
            if not obj.is_m2m or len(parent_field) > 1:
                field = self.model._meta.get_field(parent_field[0])
                try:
                    parent = field.related_model.objects.get(
                        pk=self.kwargs['pk'])
                except ObjectDoesNotExist:
                    raise Http404()
                setattr(form.instance, parent_field[0], parent)
            return form

        def get_context_data(self, **kwargs):

            obj = self.crud if hasattr(self, 'crud') else self
            context = Crud.CreateView.get_context_data(
                self, **kwargs)

            params = {'pk': self.kwargs['pk']}

            if self.container_field:
                # FIXME refatorar para parent_field com '__'
                parent_model = getattr(
                    self.model, obj.parent_field).field.related_model

                container = self.container_field.split('__')
                if len(container) > 1:
                    params['__'.join(container[1:])] = self.request.user.pk

                try:
                    parent_object = parent_model.objects.get(**params)
                except Exception as e:
                    username = self.request.user.username
                    self.logger.error("user=" + username + ". " + str(e))
                    raise Http404()
            else:
                parent_model = self.model
                parent_object = None
                if '__' in obj.parent_field:
                    fields = obj.parent_field.split('__')
                    for field in fields:
                        if parent_model == self.model:
                            parent_model = getattr(
                                parent_model, field).field.related_model
                            parent_object = parent_model.objects.get(**params)
                        else:
                            parent_object = getattr(parent_object, field)

                else:
                    parent_model = getattr(self.model, obj.parent_field)
                    if isinstance(parent_model.field, ForeignKey):
                        parent_model = parent_model.field.related_model
                    else:
                        parent_model = parent_model.rel.related_model

                    parent_object = parent_model.objects.get(**params)

                context['root_pk'] = parent_object.pk

            if parent_object:
                context['title'] = '%s <small>(%s)</small>' % (
                    context['title'], parent_object)

            return context

        @property
        def cancel_url(self):

            if hasattr(super(), 'cancel_url'):
                return super().cancel_url

            if self.list_url:
                return self.list_url
            obj = self.crud if hasattr(self, 'crud') else self

            params = {'pk': self.kwargs['pk']}

            parent_model = self.model
            parent_object = None
            if '__' in obj.parent_field:
                fields = obj.parent_field.split('__')
                for field in fields:
                    if parent_model == self.model:
                        parent_model = getattr(
                            parent_model, field).field.related_model
                        parent_object = parent_model.objects.get(**params)
                    else:
                        parent_object = getattr(parent_object, field)
                    break

            else:
                parent_model = getattr(
                    parent_model, obj.parent_field).field.related_model
                parent_object = parent_model.objects.get(**params)

            return reverse(
                '%s:%s' % (parent_model._meta.app_config.name,
                           '%s_%s' % (
                               parent_model._meta.model_name,
                               ACTION_DETAIL)),
                kwargs={'pk': parent_object.pk})

    class UpdateView(Crud.UpdateView):
        permission_required = RP_CHANGE,

        @classmethod
        def get_url_regex(cls):
            return r'^/%s/(?P<pk>\d+)/edit$' % cls.model._meta.model_name

    class DeleteView(Crud.DeleteView):
        permission_required = RP_DELETE,

        @classmethod
        def get_url_regex(cls):
            return r'^/%s/(?P<pk>\d+)/delete$' % cls.model._meta.model_name

        def get_success_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if '__' in obj.parent_field:
                fields = obj.parent_field.split('__')
                parent_object = self.object
                for field in fields:
                    parent_object = getattr(parent_object, field)
                    break
            else:
                parent_object = getattr(self.object, obj.parent_field)
            if not isinstance(parent_object, models.Model):
                if parent_object.count() > 1:
                    if 'pkk' not in self.request.GET:
                        raise Http404
                    root_pk = self.request.GET['pkk']
                    parent_object = parent_object.filter(id=root_pk)

                parent_object = parent_object.first()

                if not parent_object:
                    raise Http404
            root_pk = parent_object.pk

            pk = root_pk

            if obj.is_m2m:
                namespace = parent_object._meta.app_config.name
                return reverse('%s:%s' % (
                    namespace,
                    '%s_%s' % (parent_object._meta.model_name, ACTION_DETAIL)),
                    args=(pk,))
            else:
                return self.resolve_url(ACTION_LIST, args=(pk,))

    class DetailView(Crud.DetailView):
        permission_required = RP_DETAIL,
        template_name = 'crud/detail_detail.html'

        @classmethod
        def get_url_regex(cls):
            return r'^/%s/(?P<pk>\d+)$' % cls.model._meta.model_name

        @property
        def detail_list_url(self):
            obj = self.crud if hasattr(self, 'crud') else self

            if not obj.ListView:
                return ''

            if obj.ListView.permission_required not in obj.public or\
                    self.request.user.has_perm(self.permission(RP_LIST)):
                if '__' in obj.parent_field:
                    fields = obj.parent_field.split('__')
                    parent_object = self.object
                    for field in fields:
                        parent_object = getattr(parent_object, field)
                else:
                    parent_object = getattr(self.object, obj.parent_field)

                if not isinstance(parent_object, models.Model):
                    if parent_object.count() > 1:
                        if 'pkk' not in self.request.GET:
                            raise Http404
                        root_pk = self.request.GET['pkk']
                        parent_object = parent_object.filter(id=root_pk)

                    parent_object = parent_object.first()

                    if not parent_object:
                        raise Http404
                root_pk = parent_object.pk

                pk = root_pk
                return self.resolve_url(ACTION_LIST, args=(pk,))
            else:
                return ''

        @property
        def detail_create_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.CreateView:
                return ''

            if self.request.user.has_perm(self.permission(RP_ADD)):
                parent_field = obj.parent_field.split('__')[0]
                parent_object = getattr(self.object, parent_field)

                if not isinstance(parent_object, models.Model):
                    if parent_object.count() > 1:
                        if 'pkk' not in self.request.GET:
                            raise Http404
                        root_pk = self.request.GET['pkk']
                        parent_object = parent_object.filter(id=root_pk)

                    parent_object = parent_object.first()

                    if not parent_object:
                        raise Http404
                root_pk = parent_object.pk

                url = self.resolve_url(ACTION_CREATE, args=(root_pk,))
                if not obj.is_m2m:
                    return url
                else:
                    if '__' in obj.parent_field:
                        fields = obj.parent_field.split('__')
                        parent_object = self.object
                        for field in fields:
                            parent_object = getattr(parent_object, field)
                    else:
                        parent_object = getattr(self.object, obj.parent_field)

                        parent_object = parent_object.filter(
                            pk=root_pk).first()

                    return url + '?pkk=' + str(parent_object.pk)
            else:
                return ''

        @property
        def detail_set_create_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if hasattr(obj, 'model_set') and obj.model_set\
                    and self.request.user.has_perm(
                        self.permission_set(RP_ADD)):
                root_pk = self.object.pk
                pk = root_pk

                url = self.resolve_url_set(ACTION_CREATE, args=(pk,))
                if not obj.is_m2m:
                    return url
                else:
                    if '__' in obj.parent_field:
                        fields = obj.parent_field.split('__')
                        parent_object = self.object
                        for field in fields:
                            parent_object = getattr(parent_object, field)
                    else:
                        parent_object = getattr(self.object, obj.parent_field)

                    return url + '?pkk=' + str(parent_object.pk)

            else:
                return ''

        @property
        def detail_root_detail_url(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if not obj.link_return_to_parent_field:
                return ''
            if hasattr(obj, 'parent_field'):
                parent_field = obj.parent_field.split('__')
                if not obj.is_m2m or len(parent_field) > 1:
                    # field = self.model._meta.get_field(parent_field[0])

                    if isinstance(getattr(
                            self.object, parent_field[0]), models.Model):
                        parent_object = getattr(self.object, parent_field[0])

                        root_pk = parent_object.pk
                        pk = root_pk

                        namespace = parent_object._meta.app_config.name
                        return reverse('%s:%s' % (
                            namespace,
                            '%s_%s' % (parent_object._meta.model_name,
                                       ACTION_DETAIL)),
                                       args=(pk,))
            return ''

        @property
        def detail_root_detail_verbose_name(self):
            obj = self.crud if hasattr(self, 'crud') else self
            if hasattr(obj, 'parent_field'):
                parent_field = obj.parent_field.split('__')
                if not obj.is_m2m or len(parent_field) > 1:
                    field = self.model._meta.get_field(parent_field[0])

                    return field.verbose_name
            return ''

    @classonlymethod
    def build(cls, model, parent_field, help_topic,
              _model_set=None, list_field_names=[]):
        crud = super(MasterDetailCrud, cls).build(
            model, help_topic, _model_set=_model_set,
            list_field_names=list_field_names)
        crud.parent_field = parent_field
        return crud


class CrudBaseForListAndDetailExternalAppView(MasterDetailCrud):
    CreateView, UpdateView, DeleteView = None, None, None

    class BaseMixin(Crud.PublicMixin, MasterDetailCrud.BaseMixin):

        def resolve_url(self, suffix, args=None):
            obj = self.crud if hasattr(self, 'crud') else self

            """ namespace deve ser redirecionado para app local pois
            o models colocados nos cruds que herdam este Crud são de outras app
            """
            return reverse('%s:%s' % (obj.namespace, self.url_name(suffix)),
                           args=args)
