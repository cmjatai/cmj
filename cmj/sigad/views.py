from operator import attrgetter

from braces.views import PermissionRequiredMixin, FormMessagesMixin
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.db.models.aggregates import Max
from django.http.response import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from cmj.sigad import forms, models
from cmj.sigad.models import Documento, Classe, PermissionsUserClasse, Media,\
    VersionedMedia


class DocumentoMixin(object):

    def get_initial(self):

        if 'documento_id' in self.wargs:
            parent = get_object_or_404(
                Documento, pk=self.kwargs.get('documento_id'))
            initial = {'parent': parent}

        if 'pk' in self.kwargs:
            initial['pk'] = self.kwargs.get('pk')

        return initial

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DocumentoMixin, self).dispatch(*args, **kwargs)


class ClasseCreateView(FormMessagesMixin, CreateView):
    form_valid_message = _('Classe criada com sucesso!')
    form_invalid_message = _('Existem erros no formulário de cadastro!')
    template_name = 'sigad/form.html'
    form_class = forms.ClasseForm

    @property
    def cancel_url(self):
        if 'pk' not in self.kwargs:
            return reverse_lazy('sigad:classe_list')
        else:
            return reverse_lazy(
                'sigad:subclasse_list',
                kwargs={'pk': self.kwargs['pk']})

    @property
    def title(self):
        if 'pk' not in self.kwargs:
            self.parent = None
            return _('Cadastro de Classe Geral')

        if not hasattr(self, 'parent') or (
                hasattr(self, 'parent') and
                self.kwargs['pk'] != self.parent.pk):
            self.parent = get_object_or_404(Classe, pk=self.kwargs['pk'])

        return self.parent

    def get_success_url(self):
        return reverse_lazy(
            'sigad:subclasse_list',
            kwargs={'pk': self.object.id})

    def get_initial(self):
        self.title
        if self.parent:
            self.initial = {'parent': self.parent}

            codigo__max = Classe.objects.filter(
                parent=self.parent).order_by('codigo').aggregate(Max('codigo'))

            self.initial['codigo'] = codigo__max['codigo__max'] + 1

        return CreateView.get_initial(self)

    def post(self, request, *args, **kwargs):
        self.title
        return super(ClasseCreateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.modifier = self.request.user
        self.object.parent = self.parent
        self.object.save()

        if self.object.visibilidade == models.STATUS_PUBLIC:
            parents = self.object.parents
            for p in parents:
                p.visibilidade = models.STATUS_PUBLIC
                p.save()

        return super(ClasseCreateView, self).form_valid(form)


class ClasseUpdateView(FormMessagesMixin, UpdateView):
    form_valid_message = _('Classe Alterada com sucesso!')
    form_invalid_message = _('Existem erros no formulário!')
    template_name = 'sigad/form.html'
    form_class = forms.ClasseForm
    model = Classe

    @property
    def cancel_url(self):
        return reverse_lazy(
            'sigad:subclasse_list',
            kwargs={'pk': self.kwargs['pk']})

    @property
    def title(self):
        self.parent = get_object_or_404(Classe, pk=self.kwargs['pk']).parent
        return self.parent

    def get_success_url(self):
        return reverse_lazy(
            'sigad:subclasse_list',
            kwargs={'pk': self.object.id})

    def get_initial(self):
        self.title
        if self.parent:
            self.initial = {'parent': self.parent}
        return UpdateView.get_initial(self)

    def post(self, request, *args, **kwargs):
        self.title
        return super(ClasseUpdateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.modifier = self.request.user
        self.object.parent = self.parent
        self.object.save()
        return super(ClasseUpdateView, self).form_valid(form)


class ClasseListView(PermissionRequiredMixin, ListView):
    permission_required = 'sigad.view_subclasse'

    model = Classe
    template_name = 'sigad/classe_list.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = None
        if 'pk' in self.kwargs:
            self.object = get_object_or_404(Classe, pk=self.kwargs['pk'])

            has_permission = self.check_permissions(request)

            if not has_permission:
                if not request.user.is_superuser and \
                        self.object.visibilidade != models.STATUS_PUBLIC:
                    has_permission = False

                    pubs = Classe.objects.filter(
                        visibilidade=models.STATUS_PUBLIC).select_related(
                        'parent', 'parent__parent')
                    for pub in pubs:
                        parents = pub.parents
                        for p in parents[::-1]:
                            if p == self.object:
                                has_permission = True
                                break
                        if has_permission:
                            break

                    if not has_permission and not request.user.is_anonymous():
                        if (self.object.visibilidade ==
                                models.STATUS_PRIVATE and
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
                        return self.handle_no_permission(request)

        return ListView.dispatch(self, request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        return ListView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        context['object'] = self.object

        return ListView.get_context_data(self, **context)

    def get_queryset(self):
        qpub = None
        if 'pk' not in self.kwargs:
            self.object = None
            qpub = Classe.objects.filter(parent__isnull=True)
        else:
            qpub = Classe.objects.filter(parent_id=self.kwargs['pk'])

        if self.check_permissions(self.request):
            return qpub

        qpub = qpub.filter(visibilidade=models.STATUS_PUBLIC)

        qs = list(qpub)

        ''' Inclui os filhos da classe atual de visualização que
        possuam algum herdeiro que seja público'''
        pubs = Classe.objects.filter(
            visibilidade=models.STATUS_PUBLIC).select_related(
            'parent', 'parent__parent')
        for pub in pubs:
            parents = pub.parents
            for p in parents[::-1]:
                if p.parent == self.object:
                    if p not in qs:
                        qs.append(p)

        if not self.request.user.is_anonymous():

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


class DocumentoCreateView(
        PermissionRequiredMixin,
        FormMessagesMixin,
        CreateView):
    permission_required = ('sigad.add_documento')
    form_valid_message = _('Documento criado com sucesso!')
    template_name = 'sigad/form.html'
    form_class = forms.DocumentoForm

    def get_success_url(self):
        return reverse_lazy(
            'sigad:documento_detail',
            kwargs={'pk': self.object.id})

    def post(self, request, *args, **kwargs):
        try:
            form = forms.DocumentoForm(request.POST, request.FILES, **kwargs)

            if form.is_valid():
                self.object = form.save(commit=False)
                self.object.owner = request.user
                self.object.modifier = request.user
                self.object.save()

                files = form.files.getlist('medias_file')
                for f in files:
                    dm = Documento()
                    dm.media_of = self.object
                    dm.owner = self.object.owner
                    dm.modifier = self.object.modifier
                    dm.data = self.object.data
                    dm.save()

                    vm = VersionedMedia(documento=dm)
                    vm.save()

                    m = Media(file=f)
                    m.owner = self.object.owner
                    m.vm = vm
                    m.content_type = f.content_type
                    m.save()
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        except Exception as e:
            print(e)
        return HttpResponse("post")


class DocumentoPermissionRequiredMixin(PermissionRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object:
            has_permission = True

            if not request.user.is_superuser:
                if self.object.privacidade == \
                        models.DOCUMENTO_ORIGINAL_RESTRITO:
                    has_permission = self.check_permissions(request)
                elif self.object.privacidade == models.DOCUMENTO_PRIVADO and \
                        request.user != self.object.owner:
                    has_permission = False

            if not has_permission:
                return self.handle_no_permission(request)

        if request.method.lower() in self.http_method_names:
            handler = getattr(
                self, request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(request, *args, **kwargs)


class DocumentoDetailView(DocumentoPermissionRequiredMixin, DetailView):
    permission_required = ('sigad.view_documento')
    model = Documento


class MediaDetailView(DocumentoPermissionRequiredMixin, DetailView):
    permission_required = ('sigad.view_documento_media')
    model = Documento

    def get(self, request, *args, **kwargs):
        try:
            doc = Documento.objects.get(pk=kwargs['media_id'])
            media = doc.media.last
        except Exception as e:
            raise Http404

        if 'resize' in kwargs and kwargs['resize']:
            try:
                file = media.thumbnail(kwargs['resize'])
            except Exception as e:
                file = media.file
        else:
            file = media.file

        response = HttpResponse(
            file, content_type=media.content_type)

        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0
        response['Content-Disposition'] = 'inline; filename=' + \
            media.file.name
        return response


class Pcasp2016ImportView(View):

    def get(self, request, *args, **kwargs):
        import csv
        csvfile = open(
            '/home/leandro/Downloads/sigad/PCASP_Estendido_2016_errata.csv')
        reader = csv.DictReader(csvfile)

        def nivel(conta):
            nv = len(conta)
            if not nv:
                return 0

            if nv > 0 and conta[-1]:
                return nv
            return nivel(conta[:-1])

        classe = None
        nv_old = 0
        for row in reader:
            conta = [int('0' + sv) for sv in row['CONTA'].split('.')]
            titulo = row['TÍTULO'].replace(
                '\n', '').replace('  ', '').replace('–', '-')

            funcao = row['FUNÇÃO'].replace(
                '\n', '').replace('  ', '').replace('–', '-')

            if conta >= [2, 1, 5, 0, 0, 0, 0]:
                print(conta)

            nv = nivel(conta)
            if nv == 1:
                parent = None
            elif not nv:
                continue

            if nv_old < nv:
                parent = classe
            elif nv_old > nv:
                parent = classe
                while nv_old >= nv:
                    nv_old = parent.nivel
                    parent = parent.parent

            classe = Classe()
            classe.owner = request.user
            classe.modifier = request.user
            classe.codigo = conta[nv - 1]
            classe.nome = titulo
            classe.descricao = funcao
            classe.visibilidade = models.STATUS_RESTRICT
            classe.perfil = models.CLASSE_ESTRUTURAL
            classe.parent = parent
            classe.clean()
            classe.save()

            nv_old = nv

        classes = Classe.objects.select_related('parent', 'parent__parent')

        for cls in classes:
            if cls.subclasses.exists():
                cls.perfil = models.CLASSE_ESTRUTURAL
            else:
                cls.perfil = models.CLASSE_DOCUMENTAL
            cls.save()

        content = ''
        for row in reader:
            conta = [int('0' + sv) for sv in row['CONTA'].split('.')]
            titulo = row['TÍTULO'].replace(
                '\n', '').replace('  ', '').replace('–', '-')

            funcao = row['FUNÇÃO'].replace(
                '\n', '').replace('  ', '').replace('–', '-')

            content += '%s - %s - %s\n' % (
                nivel(conta),
                conta,
                row['TÍTULO'].replace('\n', '').
                replace('  ', '').replace('–', '-'))

        return HttpResponse(content, content_type='text/plain; charset=utf8')
