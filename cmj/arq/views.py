
from braces.views._forms import FormMessagesMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls.base import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from cmj.arq import forms


"""
class ClasseParentMixin:
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
            return _('Cadastro de Classe Geral')

        return '%s - %s - <small>(%s)</small>' % (
            self.parent, self.parent.apelido or '', _('Cadastro de SubClasse'))

    @property
    def cancel_url(self):
        if 'pk' not in self.kwargs:
            return reverse_lazy('cmj.arq:classe_list')
        else:
            return reverse_lazy(
                'cmj.arq:subclasse_list',
                kwargs={'pk': self.kwargs['pk']})

    def get_success_url(self):
        return reverse_lazy(
            'cmj.arq:subclasse_list',
            kwargs={'pk': self.object.id})


class ClasseCreateView(ClasseParentMixin,
                       FormMessagesMixin,
                       PermissionRequiredMixin,
                       CreateView):
    permission_required = 'arq.add_classe'
    form_valid_message = _('Classe criada com sucesso!')
    form_invalid_message = _('Existem erros no formulário de cadastro!')
    template_name = 'crud/form.html'
    form_class = forms.ClasseForm
    model = Classe

    def form_valid(self, form):

        self.object = form.save(commit=False)

        self.object.owner = self.request.user

        if self.parent:
            self.object.parent = self.parent

        response = super(ClasseCreateView, self).form_valid(form)

        return response

    def get_initial(self):
        self.initial = {'parent': self.parent}

        cod__max = Classe.objects.filter(
            parent=self.parent).order_by('codigo').aggregate(Max('codigo'))

        self.initial['codigo'] = cod__max['codigo__max'] + \
            1 if cod__max['codigo__max'] else 1

        return CreateView.get_initial(self)


class ClasseUpdateView(ClasseParentMixin,
                       FormMessagesMixin,
                       PermissionRequiredMixin,
                       UpdateView):
    permission_required = 'arq.change_classe'
    form_valid_message = _('Classe Alterada com sucesso!')
    form_invalid_message = _('Existem erros no formulário!')
    template_name = 'crud/form.html'
    form_class = forms.ClasseForm
    model = Classe

    def get_initial(self):
        self.initial = {'parent': self.parent.parent}
        return UpdateView.get_initial(self)

    def form_valid(self, form):
        return super(ClasseUpdateView, self).form_valid(form)


class ClasseDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'arq.delete_classe'
    template_name = 'crud/confirm_delete.html'
    model = Classe

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        self.parent = obj.parent

        return DeleteView.post(self, request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'cmj.arq:subclasse_list',
            kwargs={'pk': self.parent.id})


class ClasseListView(ClasseParentMixin, PermissionRequiredMixin, ListView):
    permission_required = 'arq.view_subclasse'

    model = Classe
    template_name = 'arq/classe_list.html'

    @property
    def create_url(self):
        if not self.request.user.has_perm('arq.add_classe'):
            return ''
        if 'pk' not in self.kwargs:
            return reverse_lazy('cmj.arq:classe_create')
        else:
            return reverse_lazy(
                'cmj.arq:subclasse_create',
                kwargs={'pk': self.kwargs['pk']})

    @property
    def update_url(self):
        if not self.request.user.has_perm('arq.change_classe'):
            return ''
        return reverse_lazy(
            'cmj.arq:classe_edit',
            kwargs={'pk': self.kwargs['pk']})

    @property
    def delete_url(self):
        if not self.object.parent and not self.request.user.is_superuser:
            return ''
        else:
            return reverse_lazy(
                'cmj.arq:classe_delete',
                kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = {}
        context['object'] = self.object

        if self.object:
            context['subnav_template_name'] = 'arq/subnav_classe.yaml'

        return ListView.get_context_data(self, **context)

    def get_queryset(self):
        qpub = None
        if 'pk' not in self.kwargs:
            self.object = None
            qpub = Classe.objects.filter(parent__isnull=True)
        else:
            qpub = Classe.objects.filter(parent_id=self.kwargs['pk'])

        if self.has_permission():
            return qpub

        qpub = qpub.filter(visibilidade=Classe.STATUS_PUBLIC)

        qs = list(qpub)
        ''' Inclui os filhos da classe atual de visualização que
        possuam algum herdeiro que seja público'''
        pubs = Classe.objects.filter(
            visibilidade=Classe.STATUS_PUBLIC).select_related(
            'parent', 'parent__parent')
        for pub in pubs:
            parents = pub.parents
            for p in parents[::-1]:
                if p.parent == self.object:
                    if p not in qs:
                        qs.append(p)

        if not self.request.user.is_anonymous:

            ''' Seleciona todas as classes com permissões expressas e visuali-
            zação para o usuário conectado
            '''
            pr = self.permission_required.split('.')
            puc_list = PermissionsUserClasse.objects.filter(
                user=self.request.user,
                permission__content_type__app_label=pr[0],
                permission__codename=pr[1]).select_related(
                    'classe__parent', 'classe__parent__parent')

            for puc in puc_list:
                ''' Inclui no resultado a classe que possui autorização
                expressa de visualização e é filha direta da classe em
                visualizaçao'''
                if self.object == puc.classe.parent:
                    if puc.classe not in qs:
                        qs.append(puc.classe)
                        continue

                ''' Inclui todos os filhos imediatos da classe em visualiza-
                ção caso seja esta a com permissão expressa para o usuário
                conectado'''
                if self.object and self.object == puc.classe:
                    qs = qs + \
                        [sub for sub in self.object.subclasses.all()
                         if sub not in qs]
                    continue

                ''' Inclui os filhos da classe atual de visualização que
                possuam algum herdeiro que o usuário conectado possua direito
                de visualização'''
                parents = puc.classe.parents
                for p in parents[::-1]:
                    if p.parent == self.object:
                        if p not in qs:
                            qs.append(p)

        return sorted(qs, key=attrgetter('codigo'))

    def dispatch(self, request, *args, **kwargs):
        self.object = None
        if 'pk' in self.kwargs:
            self.object = get_object_or_404(Classe, pk=self.kwargs['pk'])

            has_permission = self.has_permission()

            if not has_permission:
                if not request.user.is_superuser and \
                        self.object.visibilidade != Classe.STATUS_PUBLIC:
                    has_permission = False

                    # FIXME: refatorar e analisar apartir de self.object
                    pubs = Classe.objects.filter(
                        visibilidade=Classe.STATUS_PUBLIC).select_related(
                        'parent', 'parent__parent')
                    for pub in pubs:
                        parents = pub.parents
                        for p in parents[::-1]:
                            if p == self.object:
                                has_permission = True
                                break
                        if has_permission:
                            break

                    if not has_permission and not request.user.is_anonymous:
                        if (self.object.visibilidade ==
                                Classe.STATUS_PRIVATE and
                                self.object.owner != request.user):
                            has_permission = False
                        else:
                            pr = self.permission_required.split('.')
                            puc_list = PermissionsUserClasse.objects.filter(
                                user=request.user,
                                permission__content_type__app_label=pr[0],
                                permission__codename=pr[1]).select_related(
                                    'classe__parent', 'classe__parent__parent')
                            for puc in puc_list:
                                if puc.classe == self.object:
                                    has_permission = True
                                    break

                                parents = puc.classe.parents
                                for p in parents[::-1]:
                                    if p == self.object:
                                        has_permission = True
                                        break
                                if has_permission:
                                    break
                    if not has_permission:
                        return self.handle_no_permission()

        return ListView.dispatch(self, request, *args, **kwargs)
"""
