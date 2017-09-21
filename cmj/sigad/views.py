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

from datetime import datetime, timedelta
from operator import attrgetter

from braces.views import FormMessagesMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.urlresolvers import reverse_lazy
from django.db.models.aggregates import Max
from django.http.response import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView, MultipleObjectMixin
from sapl.parlamentares.models import Parlamentar
import reversion

from cmj.crud.base import MasterDetailCrud
from cmj.sigad import forms, models
from cmj.sigad.forms import DocumentoForm
from cmj.sigad.models import Documento, Classe, ReferenciaEntreDocumentos,\
    PermissionsUserClasse, PermissionsUserDocumento, Revisao, CMSMixin
from cmj.utils import make_pagination


class PathView(MultipleObjectMixin, TemplateView):
    template_name = 'base_path.html'
    documento = None
    classe = None
    paginate_by = 30

    def get(self, request, *args, **kwargs):

        print(self.kwargs['slug'])

        if self.documento and self.documento.tipo == Documento.TPD_IMAGE:
            try:
                midia = self.documento.midia.last
            except Exception as e:
                raise Http404

            if 'resize' in kwargs and kwargs['resize']:
                try:
                    file = midia.thumbnail(kwargs['resize'])
                except Exception as e:
                    file = midia.file
            else:
                file = midia.file

            response = HttpResponse(
                file, content_type=midia.content_type)

            response['Cache-Control'] = 'no-cache'
            response['Pragma'] = 'no-cache'
            response['Expires'] = 0
            response['Content-Disposition'] = 'inline; filename=' + \
                midia.file.name
            return response

        return TemplateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        if not self.documento and not self.classe:
            return TemplateView.get_context_data(self, **kwargs)

        if self.documento:
            context = TemplateView.get_context_data(self, **kwargs)

            parlamentares = self.documento.parlamentares.all()

            next = Documento.objects.view_public_docs().filter(
                public_date__gte=self.documento.public_date,
                classe=self.documento.classe,
            ).exclude(
                id=self.documento.id).last()
            context['next'] = next

            previous = Documento.objects.view_public_docs().filter(
                public_date__lte=self.documento.public_date,
                classe=self.documento.classe,
            ).exclude(
                id=self.documento.id).first()
            context['previous'] = previous

            docs = Documento.objects.view_public_docs(
            ).exclude(id=self.documento.id)

            if parlamentares.exists():
                docs = docs.filter(
                    parlamentares__in=parlamentares)
            else:
                docs = docs.filter(parlamentares__isnull=True)

            if parlamentares.count() > 4:
                docs = docs.distinct(
                    'parlamentares__id').order_by('parlamentares__id')

            context['object_list'] = docs[:4]

        elif self.classe:
            template = self.classe.template_classe
            if template == models.CLASSE_TEMPLATES_CHOICE.lista_em_linha:
                kwargs['object_list'] = self.classe.documento_set.filter(
                    public_date__isnull=False).order_by(
                    '-public_date').all()
            elif template == models.CLASSE_TEMPLATES_CHOICE.galeria:
                kwargs['object_list'] = Documento.objects.filter(
                    tipo=Documento.TPD_GALLERY)

            self.object_list = kwargs['object_list']
            context = super().get_context_data(**kwargs)

            if self.paginate_by:
                page_obj = context['page_obj']
                paginator = context['paginator']
                context['page_range'] = make_pagination(
                    page_obj.number, paginator.num_pages)

        context['object'] = self.documento if self.documento else self.classe
        context['path'] = '-path'

        return context

    def busca_doc_slug(self, slug):
        # busca documento dentro de classes de nivel > 1
        for i, item in enumerate(slug):
            try:
                slug_part = slug[:i + 1]
                slug_part.reverse()
                slug_class = slug[i + 1:]
                slug_class.reverse()
                # print(slug_class, slug_part)
                return Documento.objects.get(
                    slug='/'.join(slug_part),
                    classe__slug='/'.join(slug_class))
                break
            except:
                pass
        return None

    def dispatch(self, request, *args, **kwargs):

        slug = kwargs.get('slug', '')

        slug = slug.split('/')
        slug = [s for s in slug if s]

        if not slug:
            # FIXME - pagina inicial
            return redirect('/noticias')
            self.template_name = 'path/pagina_inicial.html'
            return TemplateView.dispatch(self, request, *args, **kwargs)

        referente = None
        try:
            # verifica se o slug é uma classe
            self.classe = Classe.objects.get(slug='/'.join(slug))
        except:

            try:
                # se documento é filho de uma classe de primeiro nivel
                self.documento = Documento.objects.get(
                    slug=slug[-1],
                    classe__slug='/'.join(slug[:-1]))
            except:

                slug.reverse()

                self.documento = self.busca_doc_slug(slug)

                # se nao encontrou, verifica se é um slug por referencia
                if not self.documento:
                    slug_ref = slug[1:]
                    self.documento = self.busca_doc_slug(slug_ref)

                    if self.documento:
                        try:
                            ref = ReferenciaEntreDocumentos.objects.get(
                                slug=slug[0])
                            self.documento = ref.referenciado
                            referente = ref.referente
                        except:
                            pass

        if self.documento and self.documento.tipo not in (Documento.TPD_DOC,
                                                          Documento.TPD_IMAGE):
            raise Http404()

        if not self.documento and not self.classe:
            raise Http404()

        if self.documento:
            if self.documento.template_doc:
                self.template_name = models.DOC_TEMPLATES_CHOICE_FILES[
                    self.documento.template_doc]
            else:
                self.template_name = models.DOC_TEMPLATES_CHOICE_FILES[
                    self.documento.classe.template_doc_padrao]
        else:
            self.template_name = models.CLASSE_TEMPLATES_CHOICE_FILES[
                self.classe.template_classe]

        obj = [self.documento if self.documento else self.classe,
               'view_documento' if self.documento else 'view_pathclasse']

        if referente:
            if obj[0].visibilidade != CMSMixin.STATUS_PRIVATE:
                obj[0] = referente
            else:
                raise Http404()

        if obj[0]:
            u = request.user
            if u.is_anonymous() and obj[0].visibilidade != \
                    CMSMixin.STATUS_PUBLIC:
                raise Http404()

            elif obj[0].visibilidade == CMSMixin.STATUS_PRIVATE:
                if obj[0].owner != request.user:
                    raise Http404()
                if not request.user.has_perm('sigad.' + obj[1]):
                    raise PermissionDenied()

            elif obj[0].visibilidade == CMSMixin.STATUS_RESTRICT:

                parent = obj[0]

                while parent and not parent.permissions_user_set.exists():
                    parent = parent.parent

                if not parent and obj[0].__class__ == Documento:
                    parent = obj[0].classe

                    while parent and not parent.permissions_user_set.exists():
                        parent = parent.parent

                if parent:
                    if parent.permissions_user_set.filter(
                            user=request.user,
                            permission__codename=obj[1]).exists():
                        pass
                    elif parent.permissions_user_set.filter(
                        user__isnull=True,
                        permission__codename=obj[1]).exists() and\
                            request.user.has_perm('sigad.' + obj[1]):
                        pass
                    else:
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

        # Revisao.gerar_revisao(self.object, self.request.user)
        if self.object.visibilidade == Classe.STATUS_PUBLIC:
            parents = self.object.parents
            for p in parents:
                p.visibilidade = Classe.STATUS_PUBLIC
                p.save()
                # Revisao.gerar_revisao(p, self.request.user)

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
        # Revisao.gerar_revisao(form.instance, self.request.user)
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

        if self.object:
            if self.object.visibilidade == Classe.STATUS_RESTRICT:
                context['subnav_template_name'] = 'sigad/subnav_classe.yaml'

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

                    if not has_permission and not request.user.is_anonymous():
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


class PermissionsUserDocumentoCrud(MasterDetailCrud):
    model = PermissionsUserDocumento
    parent_field = 'documento'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['permission',  'user', ]

        def get_context_data(self, **kwargs):

            ctxt = MasterDetailCrud.BaseMixin.get_context_data(self, **kwargs)

            ctxt['subnav_template_name'] = 'sigad/subnav_documento.yaml'

            return ctxt


class PermissionsUserClasseCrud(MasterDetailCrud):
    model = PermissionsUserClasse
    parent_field = 'classe'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = ['permission',  'user', ]

        def get_context_data(self, **kwargs):

            ctxt = MasterDetailCrud.BaseMixin.get_context_data(self, **kwargs)

            if 'pk' in self.kwargs:
                ctxt['subnav_template_name'] = 'sigad/subnav_classe.yaml'

            return ctxt


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
"""

"""
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
        

class MediaDetailView(DocumentoPermissionRequiredMixin, DetailView):
    permission_required = ('sigad.view_documento_media')
    model = Documento

    def get(self, request, *args, **kwargs):
        try:
            doc = Documento.objects.get(pk=kwargs['media_id'])
            midia = doc.midia.last
        except Exception as e:
            raise Http404

        if 'resize' in kwargs and kwargs['resize']:
            try:
                file = midia.thumbnail(kwargs['resize'])
            except Exception as e:
                file = midia.file
        else:
            file = midia.file

        response = HttpResponse(
            file, content_type=midia.content_type)

        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0
        response['Content-Disposition'] = 'inline; filename=' + \
            midia.file.name
        return response

"""


class DocumentoPermissionRequiredMixin(PermissionRequiredMixin):

    def has_permission(self):
        self.object = self.get_object()
        has_permission = True
        if self.object:
            if not self.request.user.is_superuser:

                # se documento é privado e usuário que acessá não é o dono
                # não terá permissão.
                if self.object.visibilidade == Documento.STATUS_PRIVATE and \
                        self.request.user != self.object.owner:
                    has_permission = False

                # se documento é público, testa se usuário tem permissão.
                elif self.object.visibilidade == Documento.STATUS_PUBLIC:
                    has_permission = super().has_permission()

                # se documento é restrito, analisa quais usuários possuem
                # permission_required para o documento
                elif self.object.visibilidade == Documento.STATUS_RESTRICT:

                    perms = self.get_permission_required()

                    for perm in perms:
                        perm = perm.split('.')

                        if not PermissionsUserDocumento.objects.filter(
                                permission__content_type__app_label=perm[0],
                                permission__codename=perm[1],
                                user=self.request.user,
                                documento=self.object).exists():
                            has_permission = False
                            break

        return has_permission


class DocumentoDetailView(DocumentoPermissionRequiredMixin, DetailView):
    permission_required = ('sigad.view_documento')
    model = Documento


class DocumentoDeleteView(DocumentoPermissionRequiredMixin, DeleteView):
    permission_required = ('sigad.delete_documento')
    model = Documento
    template_name = 'crud/confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy(
            'cmj.sigad:path_view',
            kwargs={'slug': self.object.classe.slug})

    def documento_permitido(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.parte_de_documento():
            parent = self.object.parent
            while parent.parent and parent.parte_de_documento():
                parent = parent.parent

            messages.error(
                self.request,
                _('Parte de Documentos não são excluidos '
                  'via Exclusão de Documento'))
            return False, redirect(reverse_lazy(
                'cmj.sigad:path_view',
                kwargs={'slug': parent.absolute_slug}))

        return True, None

    def get(self, request, *args, **kwargs):
        documento_permitido = self.documento_permitido(
            request, *args, **kwargs)

        if documento_permitido[0]:
            return DeleteView.get(self, request, *args, **kwargs)
        else:
            return documento_permitido[1]

    def delete_doc(self, doc):
        # trans  midia, caso exista, para ult rev de cada descendente

        childs = doc.childs.view_childs()

        for child in childs:
            self.delete_doc(child)

        ultima_revisao = doc.revisoes.first()
        if not ultima_revisao:
            ultima_revisao = Revisao.gerar_revisao(doc, self.request.user)

        if hasattr(doc, 'midia'):
            midia = doc.midia

            midia.documento = None
            midia.revisao = ultima_revisao
            midia.save()

    def delete(self, request, *args, **kwargs):
        documento_permitido = self.documento_permitido(
            request, *args, **kwargs)

        if not documento_permitido[0]:
            return documento_permitido[1]

        self.delete_doc(self.object)

        return DeleteView.delete(self, request, *args, **kwargs)


class DocumentoUpdateView(DocumentoPermissionRequiredMixin, UpdateView):
    permission_required = ('sigad.change_documento')
    model = Documento
    form_class = DocumentoForm
    template_name = 'crud/form.html'

    @property
    def cancel_url(self):
        return self.get_success_url()

    def get_success_url(self):
        return reverse_lazy(
            'cmj.sigad:path_view',
            kwargs={'slug': self.object.absolute_slug})

    def get_context_data(self, **kwargs):

        ctxt = UpdateView.get_context_data(self, **kwargs)
        if 'pk' in self.kwargs and self.object.visibilidade == \
                Documento.STATUS_RESTRICT:
            ctxt['subnav_template_name'] = 'sigad/subnav_documento.yaml'
        return ctxt

#    def form_valid(self, form):
#        Revisao.gerar_revisao(form.instance, self.request.user)
#        return super(DocumentoUpdateView, self).form_valid(form)
