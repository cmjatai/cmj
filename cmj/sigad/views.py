"""
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
"""

from operator import attrgetter

from braces.views import FormMessagesMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.db.models.aggregates import Max
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from sapl.parlamentares.models import Partido

from cmj.sigad import forms, models
from cmj.sigad.models import Classe, Revisao, PermissionsUserClasse


class PathView(TemplateView):
    template_name = 'base_path.html'
    documento = None
    classe = None

    def get(self, request, *args, **kwargs):

        print(self.kwargs['slug'])
        #p = Partido()
        # p.save()

        return TemplateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)

        if self.documento:
            context['title'] = 'documento'
        elif self.classe:
            context['title'] = self.classe.titulo

        return context

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.get('slug', '')

        if slug:
            print(slug)
            slug = slug.split('/')
            try:
                self.classe = Classe.objects.get(slug=slug[-1])
            except:
                pass

        if not slug:
            self.template_name = 'path/pagina_inicial.html'
            return TemplateView.dispatch(self, request, *args, **kwargs)

        if not self.documento and not self.classe:
            raise Http404()

        return TemplateView.dispatch(self, request, *args, **kwargs)


class ClasseParentMixin:
    _parent = None

    @property
    def parent(self):
        if 'pk' not in self.kwargs:
            self._parent = None
            return None

        if not self._parent or (self._parent and
                                self._parent.pk != self.kwargs['pk']):
            self._parent = get_object_or_404(Classe, pk=self.kwargs['pk'])

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

        return '%s <small>(%s)</small>' % (
            self.parent, _('Cadastro de SubClasse'))

    @property
    def cancel_url(self):
        if 'pk' not in self.kwargs:
            return reverse_lazy('cmj.sigad:classe_list')
        else:
            return reverse_lazy(
                'cmj.sigad:subclasse_list',
                kwargs={'pk': self.kwargs['pk']})

    def get_success_url(self):
        return reverse_lazy(
            'cmj.sigad:subclasse_list',
            kwargs={'pk': self.object.id})


class ClasseCreateView(ClasseParentMixin,
                       FormMessagesMixin,
                       PermissionRequiredMixin,
                       CreateView):
    permission_required = 'sigad.add_classe'
    form_valid_message = _('Classe criada com sucesso!')
    form_invalid_message = _('Existem erros no formulário de cadastro!')
    template_name = 'sigad/form.html'
    form_class = forms.ClasseForm
    model = Classe

    def form_valid(self, form):

        self.object = form.save(commit=False)

        self.object.owner = self.request.user

        if self.parent:
            self.object.parent = self.parent

        response = super(ClasseCreateView, self).form_valid(form)

        Revisao.gerar_revisao(self.object, self.request.user)
        if self.object.visibilidade == models.STATUS_PUBLIC:
            parents = self.object.parents
            for p in parents:
                p.visibilidade = models.STATUS_PUBLIC
                p.save()
                Revisao.gerar_revisao(p, self.request.user)

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
    permission_required = 'sigad.change_classe'
    form_valid_message = _('Classe Alterada com sucesso!')
    form_invalid_message = _('Existem erros no formulário!')
    template_name = 'sigad/form.html'
    form_class = forms.ClasseForm
    model = Classe

    def get_initial(self):
        self.initial = {'parent': self.parent.parent}
        return UpdateView.get_initial(self)

    def form_valid(self, form):
        Revisao.gerar_revisao(form.instance, self.request.user)
        return super(ClasseUpdateView, self).form_valid(form)


class ClasseListView(ClasseParentMixin, PermissionRequiredMixin, ListView):
    permission_required = 'sigad.view_subclasse'

    model = Classe
    template_name = 'sigad/classe_list.html'

    @property
    def create_url(self):
        if not self.request.user.has_perm('sigad.add_classe'):
            return ''
        if 'pk' not in self.kwargs:
            return reverse_lazy('cmj.sigad:classe_create')
        else:
            return reverse_lazy(
                'cmj.sigad:subclasse_create',
                kwargs={'pk': self.kwargs['pk']})

    @property
    def update_url(self):
        if not self.request.user.has_perm('sigad.change_classe'):
            return ''
        return reverse_lazy(
            'cmj.sigad:classe_edit',
            kwargs={'pk': self.kwargs['pk']})

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

        if self.has_permission():
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

    def dispatch(self, request, *args, **kwargs):
        self.object = None
        if 'pk' in self.kwargs:
            self.object = get_object_or_404(Classe, pk=self.kwargs['pk'])

            has_permission = self.has_permission()

            if not has_permission:
                if not request.user.is_superuser and \
                        self.object.visibilidade != models.STATUS_PUBLIC:
                    has_permission = False

                    # FIXME: refatorar e analisar apartir de self.object
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


class DocumentoPmImportView(TemplateView):

    template_name = 'path/pagina_inicial.html'

    def get(self, request, *args, **kwargs):

        if not request.user.is_superuser:
            raise Http404()

        import urllib3
        import json

        http = urllib3.PoolManager()

        p = 1
        s = 100
        news = []
        while True:
            print(p)
            r = http.request('GET', ('www.camarajatai.go.gov.br'
                                     '/portal/json/jsonclient/json'
                                     '?page=%s&step=%s') % (
                p, s))

            jdata = json.loads(r.data.decode('utf-8'))

            for n in jdata:
                news.append(n)

            if len(jdata) < s:
                break
            p += 1

        return TemplateView.get(self, request, *args, **kwargs)

"""

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

"""
