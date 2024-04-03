from operator import attrgetter

from braces.views._forms import FormMessagesMixin
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.aggregates import Max
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls.base import reverse_lazy
from django.utils import formats, timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from haystack.views import SearchView

from cmj.arq import forms
from cmj.arq.models import ArqClasse, ArqDoc
from cmj.mixins import CheckCheckMixin
from sapl.crud.base import CrudDetailView, CrudBaseMixin


class ArqClasseParentMixin(CheckCheckMixin):
    _parent = None

    @property
    def parent(self):
        if 'pk' not in self.kwargs:
            self._parent = None
            return None

        if not self._parent or (self._parent and
                                self._parent.pk != self.kwargs['pk']):
            self._parent = get_object_or_404(self.model, pk=self.kwargs['pk'])

        return self._parent

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural

    @property
    def title(self):
        if not self.parent:
            return _('Cadastro de ArqClasse Geral')

        return '%s<br><small>(%s)</small>' % (
            self.parent, _('Cadastro de SubArqClasse'))

    @property
    def cancel_url(self):
        if 'pk' not in self.kwargs:
            return reverse_lazy('cmj.arq:arqclasse_list')
        else:
            return reverse_lazy(
                'cmj.arq:subarqclasse_list',
                kwargs={'pk': self.kwargs['pk']})

    def get_success_url(self):
        return reverse_lazy(
            'cmj.arq:subarqclasse_list',
            kwargs={'pk': self.object.id})


class ArqClasseCreateView(ArqClasseParentMixin,
                          FormMessagesMixin,
                          PermissionRequiredMixin,
                          CreateView):
    permission_required = 'arq.add_arqclasse',
    form_valid_message = _('ArqClasse criada com sucesso!')
    form_invalid_message = _('Existem erros no formulário de cadastro!')
    template_name = 'crud/form.html'
    form_class = forms.ArqClasseForm
    model = ArqClasse

    def form_valid(self, form):

        self.object = form.save(commit=False)

        self.object.owner = self.request.user

        if self.parent:
            self.object.parent = self.parent

        response = super(ArqClasseCreateView, self).form_valid(form)

        return response

    def get_initial(self):
        self.initial = {'parent': self.parent}

        cod__max = ArqClasse.objects.filter(
            parent=self.parent).order_by('codigo').aggregate(Max('codigo'))

        self.initial['codigo'] = cod__max['codigo__max'] + \
            1 if cod__max['codigo__max'] else 1

        return CreateView.get_initial(self)


class ArqClasseUpdateView(ArqClasseParentMixin,
                          FormMessagesMixin,
                          PermissionRequiredMixin,
                          UpdateView):
    permission_required = 'arq.change_arqclasse',
    form_valid_message = _('ArqClasse Alterada com sucesso!')
    form_invalid_message = _('Existem erros no formulário!')
    template_name = 'crud/form.html'
    form_class = forms.ArqClasseForm
    model = ArqClasse

    def get_initial(self):
        self.initial = {'parent': self.parent.parent}
        return UpdateView.get_initial(self)

    def form_valid(self, form):
        return super(ArqClasseUpdateView, self).form_valid(form)


class ArqClasseDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'arq.delete_arqclasse',
    template_name = 'crud/confirm_delete.html'
    model = ArqClasse

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        self.parent = obj.parent

        return DeleteView.post(self, request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'cmj.arq:subarqclasse_list',
            kwargs={'pk': self.parent.id})


class ArqClasseListView(ArqClasseParentMixin, PermissionRequiredMixin, ListView):
    permission_required = 'arq.view_arqclasse',

    model = ArqClasse
    template_name = 'arq/arqclasse_list.html'

    def get(self, request, *args, **kwargs):
        self.view_format = request.GET.get('view', 'table')

        toggle_padlock = request.GET.get('toggle_padlock', None)

        if toggle_padlock is not None:
            if not request.user.is_superuser:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _('Seu usuário não possui permissão para Trancar/Destrancar ArqClasse')
                )

            if 'pk' in self.kwargs:
                if request.user.is_superuser:
                    self.object.checkcheck = not self.object.checkcheck
                    self.object.save()

                return redirect('{}?view={}'.format(
                    reverse_lazy('cmj.arq:subarqclasse_list',
                                 kwargs={'pk': self.kwargs['pk']}),
                    self.view_format
                ))

        if self.view_format == 'tree2':
            if 'pk' in self.kwargs:
                return redirect('{}?view=tree'.format(reverse_lazy(
                    'cmj.arq:subarqclasse_list',
                    kwargs={'pk': self.kwargs['pk']})))

        if self.view_format.startswith('tree'):
            self.template_name = 'arq/arqclasse_tree.html'

        return ListView.get(self, request, *args, **kwargs)

    @property
    def create_url(self):
        if not self.request.user.has_perm('arq.add_arqclasse'):
            return ''
        if 'pk' not in self.kwargs:
            return reverse_lazy('cmj.arq:arqclasse_create')
        else:
            return reverse_lazy(
                'cmj.arq:subarqclasse_create',
                kwargs={'pk': self.kwargs['pk']})

    @property
    def update_url(self):
        if not self.request.user.has_perm('arq.change_arqclasse'):
            return ''
        return reverse_lazy(
            'cmj.arq:arqclasse_edit',
            kwargs={'pk': self.kwargs['pk']})

    @property
    def delete_url(self):
        if not self.object.parent and not self.request.user.is_superuser:
            return ''
        else:
            return reverse_lazy(
                'cmj.arq:arqclasse_delete',
                kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = {}
        context['object'] = self.object

        context['view_format'] = self.view_format

        context['title'] = self.object

        # if self.object:
        #    context['subnav_template_name'] = 'arq/subnav_classe.yaml'

        return ListView.get_context_data(self, **context)

    def get_queryset(self):
        qpub = None
        if 'pk' not in self.kwargs:
            self.object = None
            qpub = ArqClasse.objects.filter(parent__isnull=True)
        else:
            qpub = ArqClasse.objects.filter(parent_id=self.kwargs['pk'])

        return qpub

        #qpub = qpub.filter(visibilidade=ArqClasse.STATUS_PUBLIC)

        qs = list(qpub)
        pubs = ArqClasse.objects.all().select_related(
            'parent', 'parent__parent')
        for pub in pubs:
            parents = pub.parents
            for p in parents[::-1]:
                if p.parent == self.object:
                    if p not in qs:
                        qs.append(p)

        return sorted(qs, key=attrgetter('codigo'))

    def dispatch(self, request, *args, **kwargs):
        self.object = None
        if 'pk' in self.kwargs:
            self.object = get_object_or_404(ArqClasse, pk=self.kwargs['pk'])

        return super().dispatch(request, *args, **kwargs)


class ArqDocMixin(CheckCheckMixin):

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural

    @property
    def title(self):
        if 'pk' not in self.kwargs:
            return _('Cadastro de ArqDocumento')

        return '%s<br><small>(%s)</small>' % (
            self.object.titulo, _('Edição de ArqDocumento'))

    @property
    def cancel_url(self):
        return reverse_lazy(
            'cmj.arq:subarqclasse_list',
            kwargs={'pk': self.kwargs['classe_id']})

    def get_success_url(self):
        return reverse_lazy(
            'cmj.arq:arqdoc_detail',
            kwargs={
                'classe_id': self.kwargs['classe_id'],
                'pk': self.object.id
            })


class ArqDocUpdateView(ArqDocMixin, FormMessagesMixin,
                       PermissionRequiredMixin,
                       UpdateView):
    permission_required = 'arq.change_arqdoc',
    form_valid_message = _('ArqDoc alterado com sucesso!')
    form_invalid_message = _('Existem erros no formulário!')
    template_name = 'crud/form.html'
    form_class = forms.ArqDocForm
    model = ArqDoc

    def get_initial(self):

        initial = super().get_initial()
        initial['request_user'] = self.request.user
        initial['classe_estrutural'] = self.kwargs['classe_id']
        return initial


class ArqDocDetailView(CrudBaseMixin, CrudDetailView, ArqDocMixin, ):
    permission_required = 'arq.detail_arqdoc',
    template_name = 'arq/arqdoc_detail.html'
    model = ArqDoc
    layout_key = 'ArqDocDetail'

    @property
    def list_url(self):
        return self.cancel_url

    @property
    def create_url(self):
        return reverse_lazy(
            'cmj.arq:arqdoc_create',
            kwargs={'classe_id': self.kwargs['classe_id']})

    @property
    def update_url(self):
        return reverse_lazy(
            'cmj.arq:arqdoc_edit',
            kwargs={
                'pk': self.object.pk,
                'classe_id': self.kwargs['classe_id']
            })

    @property
    def delete_url(self):
        return reverse_lazy(
            'cmj.arq:arqdoc_delete',
            kwargs={
                'pk': self.object.pk,
                'classe_id': self.kwargs['classe_id']
            })

    @property
    def title(self):
        o = self.object
        return '%s<br><small><small>%s%s<br>%s%s</small></small>' % (
            o.titulo,
            _('ArqClasse Estrutural -> '),
            o.classe_estrutural,
            (_('ArqClasse Lógica -> ') if o.classe_logica else ''),
            o.classe_logica or ''
        )

    def hook_conta(self, obj):
        return 'Conta', str(obj.conta)

    def hook_owner(self, obj):
        return 'Criado Por', str(obj.owner)

    def hook_created(self, obj):
        return 'Em', formats.date_format(timezone.localtime(obj.created), "d/m/Y - H:i:s")

    def hook_modifier(self, obj):
        return 'Última Alteração', str(obj.modifier)

    def hook_modified(self, obj):
        return 'Em', formats.date_format(timezone.localtime(obj.modified), "d/m/Y - H:i:s")

    def hook_pagina1(self, obj):
        return 'Primeira Página do Docuemnto', f'''
            <div class="d-flex justify-content-center p-2">
                <img class="img-fluid w-50" src="/api/arq/arqdoc/{obj.id}/arquivo/?page=1&dpi=300"
            </div>
        '''

    def get(self, request, *args, **kwargs):
        self.view_format = request.GET.get('view', 'table')
        toggle_padlock = request.GET.get('toggle_padlock', None)

        if toggle_padlock is not None and request.user.is_superuser:
            if 'pk' in self.kwargs:
                self.object = self.get_object()
                self.object.checkcheck = not self.object.checkcheck
                self.object.save()
                return redirect(
                    reverse_lazy(
                        'cmj.arq:arqdoc_detail',
                        kwargs={
                            'pk': self.object.pk,
                            'classe_id': self.kwargs['classe_id']
                        })
                )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = CrudDetailView.get_context_data(self, **kwargs)
        context['view_format'] = self.view_format
        return context


class ArqDocCreateView(ArqDocMixin, FormMessagesMixin,
                       PermissionRequiredMixin,
                       CreateView):
    permission_required = 'arq.add_arqdoc',
    form_valid_message = _('ArqDoc criado com sucesso!')
    form_invalid_message = _('Existem erros no formulário!')
    #template_name = 'crud/form.html'
    form_class = forms.ArqDocForm
    model = ArqDoc

    def is_checkcheck(self):
        # check check da classe

        try:
            ac = ArqClasse.objects.get(pk=self.kwargs['classe_id'])
        except ObjectDoesNotExist:
            raise Http404()

        return ac.checkcheck

    def get_initial(self):

        initial = super().get_initial()
        initial['request_user'] = self.request.user

        initial['classe_estrutural'] = self.kwargs['classe_id']

        cod__max = ArqDoc.objects.filter(
            classe_estrutural=self.kwargs['classe_id']
        ).order_by('codigo').aggregate(Max('codigo'))

        initial['codigo'] = cod__max['codigo__max'] + \
            1 if cod__max['codigo__max'] else 1

        return initial


class ArqDocDeleteView(ArqDocMixin,
                       PermissionRequiredMixin,
                       DeleteView):
    permission_required = 'arq.delete_arqdoc',
    model = ArqDoc
    template_name = 'crud/confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy(
            'cmj.arq:subarqclasse_list',
            kwargs={'pk': self.object.classe_estrutural_id})
