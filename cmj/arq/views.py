
from operator import attrgetter

from braces.views._forms import FormMessagesMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.aggregates import Max
from django.shortcuts import get_object_or_404, redirect
from django.urls.base import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from cmj.arq import forms
from cmj.arq.models import ArqClasse


class ArqClasseParentMixin:
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

        return '%s - %s - <small>(%s)</small>' % (
            self.parent, self.parent.titulo or '', _('Cadastro de SubArqClasse'))

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
    permission_required = 'arq.add_arqclasse'
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
    permission_required = 'arq.change_arqclasse'
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
    permission_required = 'arq.delete_arqclasse'
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
    permission_required = 'arq.view_subarqclasse'

    model = ArqClasse
    template_name = 'arq/arqclasse_list.html'

    def get(self, request, *args, **kwargs):
        self.view_format = request.GET.get('view', 'table')

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

        # if self.has_permission():
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
