import base64
import io
from operator import attrgetter
import tempfile
import zipfile

from braces.views import FormMessagesMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import F, Q
from django.db.models.aggregates import Max, Count
from django.http.response import Http404, HttpResponse, HttpResponseForbidden,\
    HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls.base import reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView, MultipleObjectMixin
from haystack.forms import model_choices
from haystack.query import SearchQuerySet
from haystack.utils.app_loading import haystack_get_model,\
    haystack_get_models

from cmj import globalrules
from cmj.core.models import AreaTrabalho, CertidaoPublicacao
from cmj.sigad import forms, models
from cmj.sigad.forms import DocumentoForm, CaixaPublicacaoForm
from cmj.sigad.models import Documento, Classe, ReferenciaEntreDocumentos,\
    PermissionsUserClasse, PermissionsUserDocumento, Revisao, CMSMixin,\
    CLASSE_TEMPLATES_CHOICE, CaixaPublicacao, CaixaPublicacaoClasse,\
    CaixaPublicacaoRelationship, UrlShortener
from cmj.utils import make_pagination
from sapl.crud.base import MasterDetailCrud, Crud
from sapl.parlamentares.models import Parlamentar, Legislatura,\
    AfastamentoParlamentar


class TabIndexMixin:
    _tabindex = 0

    @property
    def tabindex(self):
        self._tabindex += 1
        return self._tabindex


class PaginaInicialView(TabIndexMixin, TemplateView):

    template_name = 'path/pagina_inicial.html'

    def get_context_data(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)
        context['path'] = '-path'

        np = self.get_noticias_dos_parlamentares()

        context['noticias_dos_parlamentares'] = np

        context['noticias_da_procuradoria'] = self.get_noticias_da_procuradoria()

        context['ultimas_publicacoes'] = self.get_ultimas_publicacoes()

        return context

    def get_noticias_da_procuradoria(self):

        docs = Documento.objects.qs_news()
        # FIXME: IMPLEMENTAR ESTRATÉGIA CORRETA PARA SELECIONAR NOTÍCIAS DA
        # PROCURADORIA
        docs = docs.filter(classe=215)

        return docs

    def get_ultimas_publicacoes_uma_por_tipo__nao_usada(self):
        search_models = model_choices()

        results = []

        for m in search_models:
            sqs = SearchQuerySet().all()
            sqs = sqs.filter(at=0)
            sqs = sqs.models(*haystack_get_models(m[0]))
            sqs = sqs.order_by('-data', '-last_update')[:5]
            if len(sqs):
                results.append(sqs[0])

        return results

    def get_ultimas_publicacoes(self):
        qs = CertidaoPublicacao.objects.all()[:20]
        r = []
        for cert in qs:
            r.append(cert)
        return r

    def get_ultimas_publicacoes__deprecated(self):
        sqs = SearchQuerySet().all()
        sqs = sqs.filter(
            Q(at=0) |
            Q(at__in=AreaTrabalho.objects.areatrabalho_publica().values_list('id', flat=True)))
        sqs = sqs.models(
            *haystack_get_models('protocoloadm.documentoadministrativo'))
        sqs = sqs.order_by('-id')[:100]

        r = []
        for sr in sqs:
            if sr.object and sr.object._certidao:
                if sr.object._certidao.exists():
                    r.append(sr)

                    if len(r) == 10:
                        break

        return r

    def get_noticias_dos_parlamentares(self):
        legislatura_atual = Legislatura.objects.first()

        docs = Documento.objects.qs_news()

        docs = docs.annotate(
            count_parlamentar=Count("parlamentares", distinct=True)
        ).filter(
            parlamentares__mandato__legislatura_id=legislatura_atual.id,
            count_parlamentar=1,
            parlamentares__ativo=True
        ).values_list('id', flat=True)

        docs = Documento.objects.filter(
            id__in=docs
        ).distinct(
            'parlamentares__id'
        ).order_by(
            'parlamentares__id', '-public_date'
        ).values_list('id', flat=True)

        docs = Documento.objects.filter(
            id__in=docs
        ).order_by(
            '-public_date'
        )

        return docs


class PathView(TabIndexMixin, MultipleObjectMixin, TemplateView):
    template_name = 'base_path.html'
    documento = None
    classe = None
    referencia = None
    paginate_by = 30

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        # print(self.kwargs['slug'])

        if self.documento:
            if self.documento.tipo in (Documento.TPD_IMAGE, Documento.TPD_FILE):
                try:
                    midia = self.documento.midia.last
                except Exception as e:
                    raise Http404

                page = kwargs.get('page', None)

                if page == 'page':
                    return TemplateView.get(self, request, *args, **kwargs)

                if 'resize' in kwargs and kwargs['resize']:
                    try:
                        file = midia.thumbnail(kwargs['resize'])
                    except Exception as e:
                        file = midia.file
                else:
                    file = midia.file

                response = HttpResponse(
                    file, content_type=midia.content_type)

                response['Cache-Control'] = 'max-age=2592000'
                if not request.user.is_anonymous:
                    if request.META.get('HTTP_REFERER', '').endswith('construct'):
                        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'

                response['Expires'] = 0
                response['Pragma'] = 'no-cache'
                response['Content-Disposition'] = 'inline; filename=' + \
                    midia.file.name
                return response

            elif self.documento.tipo == Documento.TPD_CONTAINER_FILE:
                return self.documento.build_container_file()

            elif self.documento.tipo == Documento.TPD_GALLERY and \
                    'zipfile' in request.GET:
                file_buffer = io.BytesIO()
                with zipfile.ZipFile(file_buffer, 'w') as file:
                    for f in self.documento.documentos_citados.view_childs():
                        file.write(f.midia.last.file.path,
                                   arcname='%s-%s' % (
                                       f.id,
                                       f.midia.last.file.path.split(
                                           '/')[-1]))

                response = HttpResponse(file_buffer.getvalue(),
                                        content_type='application/zip')

                response['Cache-Control'] = 'no-cache'
                response['Pragma'] = 'no-cache'
                response['Expires'] = 0
                response['Content-Disposition'] = \
                    'inline; filename=%s.zip' % self.documento.parents[0].slug

                return response

            elif self.documento.tipo == Documento.TPD_GALLERY and \
                    request.META['REQUEST_METHOD'] == 'GET':
                return HttpResponseForbidden()

        return TemplateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        if self.referencia:
            self.template_name = 'path/path_imagem.html'
            context = TemplateView.get_context_data(self, **kwargs)
            context['object'] = self.referencia

        elif self.documento:
            context = self.get_context_data_documento(**kwargs)
        elif self.classe:
            context = self.get_context_data_classe(**kwargs)
        else:
            context = TemplateView.get_context_data(self, **kwargs)
        context['path'] = '-path'

        return context

    def get_context_data_documento(self, **kwargs):
        context = TemplateView.get_context_data(self, **kwargs)

        if self.documento.tipo == Documento.TPD_GALLERY:
            self.template_name = 'path/path_gallery.html'

        elif self.documento.tipo == Documento.TPD_IMAGE:
            self.template_name = 'path/path_imagem.html'
            context['object'] = self.documento
            context['referencia'] = None
        else:
            parlamentares = self.documento.parlamentares.all()

            if hasattr(self, 'parlamentar') and self.parlamentar:
                parlamentares = parlamentares.filter(
                    pk=self.parlamentar.parlamentar.pk)

            if self.documento.public_date:

                if parlamentares:

                    next = Documento.objects.qs_news().filter(
                        public_date__gte=self.documento.public_date,
                        classe=self.documento.classe,
                        parlamentares__in=parlamentares,
                    ).exclude(
                        id=self.documento.id).last()

                    previous = Documento.objects.qs_news().filter(
                        public_date__lte=self.documento.public_date,
                        classe=self.documento.classe,
                        parlamentares__in=parlamentares,
                    ).exclude(
                        id=self.documento.id).first()
                else:

                    next = Documento.objects.qs_news().filter(
                        public_date__gte=self.documento.public_date,
                        classe=self.documento.classe,
                        parlamentares__isnull=True,
                    ).exclude(
                        id=self.documento.id).last()

                    previous = Documento.objects.qs_news().filter(
                        public_date__lte=self.documento.public_date,
                        classe=self.documento.classe,
                        parlamentares__isnull=True,
                    ).exclude(
                        id=self.documento.id).first()

            else:
                next = None
                previous = None

            context['next'] = next
            context['previous'] = previous

            docs = Documento.objects.qs_news(
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

        context['object'] = self.documento
        return context

    def get_context_data_classe(self, **kwargs):
        template = self.classe.template_classe

        if template == models.CLASSE_TEMPLATES_CHOICE.lista_em_linha:
            kwargs['object_list'] = self.classe.documento_set.qs_news(
                user=self.request.user)

        elif template == models.CLASSE_TEMPLATES_CHOICE.galeria:
            kwargs['object_list'] = Documento.objects.view_public_gallery()

        elif template == models.CLASSE_TEMPLATES_CHOICE.fotografia:
            kwargs['object_list'] = self.classe.documento_set.qs_bi(
                self.request.user)
        elif template == models.CLASSE_TEMPLATES_CHOICE.galeria_audio:
            kwargs['object_list'] = self.classe.documento_set.qs_audio_news(
                self.request.user)

        elif template == models.CLASSE_TEMPLATES_CHOICE.galeria_video:
            kwargs['object_list'] = self.classe.documento_set.qs_video_news(
                self.request.user)

        elif template == models.CLASSE_TEMPLATES_CHOICE.parlamentar:
            docs = self.classe.parlamentar.documento_set
            kwargs['object_list'] = docs.qs_news(self.request.user)
        elif models.CLASSE_TEMPLATES_CHOICE.documento_especifico:
            kwargs['object_list'] = Documento.objects.qs_news().filter(
                parlamentares__isnull=True)[:4]

        self.object_list = kwargs['object_list']

        context = super().get_context_data(**kwargs)

        if self.paginate_by:
            page_obj = context['page_obj']
            paginator = context['paginator']
            context['page_range'] = make_pagination(
                page_obj.number, paginator.num_pages)

        if self.classe.capa:
            context['object'] = self.classe.capa
            self.template_name = models.DOC_TEMPLATES_CHOICE_FILES[
                self.classe.capa.template_doc]['template_name']
        else:
            context['object'] = self.classe

        context['create_doc_url'] = models.DOC_TEMPLATES_CHOICE_FILES[
            self.classe.template_doc_padrao]['create_url']

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

        if not slug:
            raise Http404()

        if slug[0] == 'j':
            return self._dispath_url_short(slug[1:])

        result = self._pre_dispatch(request, *args, **kwargs)
        if result:
            return result

        return TemplateView.dispatch(self, request, *args, **kwargs)

    def _dispath_url_short(self, slug):
        try:
            slug = slug.split('/')
            url = UrlShortener.objects.get(
                url_short=slug[0])

            if len(slug) == 2 and slug[1] == 'qrcode':

                response = HttpResponse(url.qrcode,
                                        content_type='image/png')

                response['Cache-Control'] = 'no-cache'
                response['Pragma'] = 'no-cache'
                response['Expires'] = 0
                response['Content-Disposition'] = \
                    'inline; filename=%s.png' % slug[0]
                return response

            return redirect('/' + url.url_long, permanent=True)

        except Exception as e:
            raise Http404()

    def _pre_dispatch(self, request, *args, **kwargs):

        slug = kwargs.get('slug', '')
        # Localização do Objecto
        referente = None
        try:
            # verifica se o slug é uma classe
            self.classe = Classe.objects.get(slug=slug)
        except:
            try:
                # Verifica se é um documento
                self.documento = Documento.objects.get(slug=slug)
            except:
                try:
                    # verifica se é uma referência
                    ref = ReferenciaEntreDocumentos.objects.get(slug=slug)
                    self.documento = ref.referenciado
                    self.referencia = ref
                except:
                    try:
                        # Verifica se é um link do antigo site
                        self.documento = Documento.objects.get(
                            old_path='/' + slug)

                        if self.documento:
                            return redirect('/' + self.documento.slug)
                    except:
                        view = PaginaInicialView.as_view()(request, *args, **kwargs)
                        return view

        if self.documento and self.documento.tipo in Documento.TDp_exclude_render:
            raise Http404()

        if self.documento:
            if self.documento.template_doc:
                self.template_name = models.DOC_TEMPLATES_CHOICE_FILES[
                    self.documento.template_doc]['template_name']
            else:
                self.template_name = models.DOC_TEMPLATES_CHOICE_FILES[
                    self.documento.classe.template_doc_padrao]['template_name']
        else:
            self.template_name = models.CLASSE_TEMPLATES_CHOICE_FILES[
                self.classe.template_classe]

        obj = [self.documento if self.documento else self.classe,
               'view_documento' if self.documento else 'view_pathclasse']

        if self.referencia:
            if obj[0].visibilidade != CMSMixin.STATUS_PRIVATE:
                obj[0] = self.referencia.referente
            else:
                raise Http404()

        # Analise de Permissão
        if obj[0]:
            u = request.user
            if u.is_anonymous and obj[0].visibilidade != \
                    CMSMixin.STATUS_PUBLIC:
                raise Http404()

            elif obj[0].visibilidade == CMSMixin.STATUS_PRIVATE:
                if obj[0].owner != request.user:
                    raise Http404()
                if not request.user.has_perm('sigad.' + obj[1]):
                    raise PermissionDenied()
                # com este if acima... se um usuário perde a permissão de
                # manter tal informação, mesmo sendo o dono, não poderá
                # mais ver essa informação. ou seja, ninguem mais poderá ver
                # criar mecanismo de auditar e manter a base de dados para
                # este caso. ou talvez notificar que está revogando de que
                # existem documentos, x, y, z, etc que vão entrar para o limbo

            elif obj[0].visibilidade == CMSMixin.STATUS_RESTRICT:

                parent = obj[0]

                # independente das consultas paternas, em sendo os pais
                # doc ou classe, independe do seu status,
                # o algoritmo abaixo não permitirá mostrar algo restrito
                # só porque seu pai é público por exemplo.
                # Um pai público pode dar regra de restrição para seus filhos
                # caso estes sejam restritos e sem regras.

                # permissoes vazias significa q se comporta como regras do
                # primeiro pai que possua mapeamento
                if obj[0].__class__ == Documento and parent.raiz:
                    parent = parent.raiz

                while parent and not parent.permissions_user_set.exists():
                    parent = parent.parent

                # se é restrito, é um Documento e não tem permissões
                # customizadas até sua raiz, passa a verificar as regras de
                # sua estrutura de classe.
                if not parent and obj[0].__class__ == Documento:
                    parent = obj[0].classe

                    # Se classe imediata não tem configuração de restrição,
                    # segue o corpotamento primeira acima que tenha
                    while parent and not parent.permissions_user_set.exists():
                        parent = parent.parent

                if parent:
                    if parent.permissions_user_set.filter(
                            user=request.user,
                            permission__codename=obj[1]).exists():
                        pass
                    elif parent.permissions_user_set.filter(
                            user=request.user,
                            permission__isnull=True).exists() and\
                            request.user.has_perm('sigad.' + obj[1]):
                        pass
                    elif parent.permissions_user_set.filter(
                        user__isnull=True,
                        permission__codename=obj[1]).exists() and\
                            request.user.has_perm('sigad.' + obj[1]):
                        pass
                    elif parent.permissions_user_set.filter(
                        user__isnull=True,
                        permission__isnull=True).exists() and\
                            request.user.has_perm('sigad.' + obj[1]):
                        pass
                    elif request.user.is_superuser:
                        pass
                    else:
                        raise Http404()
                    self.parent_classe = parent
                else:
                    # Se não configurada nenhuma restrição mas o OBJ é restrito
                    # será liberado se o usuário pertencer ao grupo
                    # globalrules.GROUP_SIGAD_VIEW_STATUS_RESTRITOS

                    if request.user.groups.filter(
                        name=globalrules.GROUP_SIGAD_VIEW_STATUS_RESTRITOS
                    ).exists():
                        pass
                    else:
                        raise Http404()

    def _pre_dispatch___Old(self, request, *args, **kwargs):

        slug = kwargs.get('slug', '')

        if isinstance(slug, str):
            slug = slug.split('/')
            slug = [s for s in slug if s]
        slug = list(filter(lambda x: x, slug))

        # Localização do Objecto
        referente = None
        try:
            # verifica se o slug é uma classe
            self.classe = Classe.objects.get(slug='/'.join(slug))
        except:

            try:
                # se documento é filho de uma classe de primeiro nivel
                self.documento = Documento.objects.get(
                    slug='/'.join(slug[1:]),
                    classe__slug=slug[0])
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
                            self.referencia = ref
                        except:
                            pass

        if self.documento and self.documento.tipo in Documento.TDp_exclude_render:
            raise Http404()

        if not self.documento and not self.classe:
            raise Http404()

        if self.documento:
            if self.documento.template_doc:
                self.template_name = models.DOC_TEMPLATES_CHOICE_FILES[
                    self.documento.template_doc]['template_name']
            else:
                self.template_name = models.DOC_TEMPLATES_CHOICE_FILES[
                    self.documento.classe.template_doc_padrao]['template_name']
        else:
            self.template_name = models.CLASSE_TEMPLATES_CHOICE_FILES[
                self.classe.template_classe]

        obj = [self.documento if self.documento else self.classe,
               'view_documento' if self.documento else 'view_pathclasse']

        if self.referencia:
            if obj[0].visibilidade != CMSMixin.STATUS_PRIVATE:
                obj[0] = self.referencia.referente
            else:
                raise Http404()

        # Analise de Permissão
        if obj[0]:
            u = request.user
            if u.is_anonymous and obj[0].visibilidade != \
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


class PathParlamentarView(PathView):

    def get(self, request, *args, **kwargs):
        return PathView.get(self, request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):

        slug = kwargs.get('slug', '')

        if slug:
            self._pre_dispatch(request, *args, **kwargs)

        classe = self.classe
        # recupera classe de parlamentar avaliando permissões

        slug = 'parlamentar'
        if kwargs['parlamentar']:
            slug = 'parlamentar/' + kwargs['parlamentar']

        kwargs['slug'] = slug
        self._pre_dispatch(request, *args, **kwargs)
        self.parlamentar = self.classe

        return TemplateView.dispatch(self, request, *args, **kwargs)

    @property
    def ultimas_autorias(self):
        if self.parlamentar.parlamentar:
            return self.parlamentar.parlamentar.autor.first().autoria_set.order_by(
                '-materia__data_apresentacao')[:5]
        else:
            return []

    def get_context_data(self, **kwargs):

        if self.parlamentar.template_classe != \
                CLASSE_TEMPLATES_CHOICE.parlamentares:
            context = PathView.get_context_data(self, **kwargs)

        else:
            context = TemplateView.get_context_data(self, **kwargs)
            context['object'] = self.classe

            legislatura_ativa = int(self.request.GET.get('l', '0'))
            sl_ativa = int(self.request.GET.get('sl', '0'))
            #parlamentar_ativo = int(self.request.GET.get('p', '0'))

            legs = Legislatura.objects
            pms = Parlamentar.objects

            # if parlamentar_ativo:
            #    context['parlamentar_ativo'] = pms.get(pk=parlamentar_ativo)

            legislaturas = []
            context['legislatura_ativa'] = 0
            context['sessaolegislativa_ativa'] = 0
            for l in legs.all():

                # if l.numero < 17:
                #    continue
                l_atual = l.atual()

                if not legislatura_ativa and l.atual() or \
                        l.pk == legislatura_ativa:
                    context['legislatura_ativa'] = l

                leg = {
                    'legislatura': l,
                    'sessoes': [],
                    'parlamentares': []
                }

                fs = l.sessaolegislativa_set.first()
                for s in l.sessaolegislativa_set.all():

                    if s.pk == sl_ativa or not sl_ativa and s == fs and \
                            s.legislatura == context['legislatura_ativa']:
                        context['sessaolegislativa_ativa'] = s
                        if s.pk == sl_ativa:
                            context['legislatura_ativa'] = l

                    # if s.legislatura != context['legislatura_ativa']:
                    #    continue

                    sessao = {
                        'sessao': s, }

                    if s == context['sessaolegislativa_ativa']:
                        sessao.update({
                            'mesa': [
                                p for p in pms.filter(
                                    mandato__legislatura=l,
                                    composicaomesa__sessao_legislativa=s
                                ).annotate(
                                    cargo_mesa=F(
                                        'composicaomesa__cargo__descricao')
                                ).order_by('composicaomesa__cargo__descricao')
                            ],
                            'parlamentares': [
                                p for p in pms.filter(
                                    mandato__legislatura=l
                                ).exclude(
                                    composicaomesa__sessao_legislativa=s
                                ).order_by(
                                    '-ativo',
                                    '-mandato__data_fim_mandato',
                                    '-mandato__titular',
                                    'nome_parlamentar')
                                .annotate(
                                    data_inicio_mandato=F(
                                        'mandato__data_inicio_mandato'),
                                    data_fim_mandato=F(
                                        'mandato__data_fim_mandato'),
                                    afastado=F('afastamentoparlamentar'),
                                    titular=F('mandato__titular')
                                ).distinct()]
                        })

                    if 'parlamentares' in sessao:
                        n = timezone.now()
                        sessao['parlamentares'] = sorted(
                            list(set(sessao['parlamentares'])),
                            key=lambda x: x.nome_parlamentar)

                        for p in sessao['parlamentares']:
                            if not l_atual:
                                p.afastado = False
                                continue

                            if not p.data_inicio_mandato <= n.date() <= p.data_fim_mandato:
                                p.afastado = True
                                continue

                            if not p.afastado:
                                continue

                            af = p.afastamentoparlamentar_set.filter(
                                data_inicio__lte=n,
                                data_fim__gte=n).exists()

                            if not af:
                                p.afastado = None

                    leg['sessoes'].append(sessao)

                if not leg['sessoes'] and l == context['legislatura_ativa']:
                    for p in pms.filter(mandato__legislatura=l):
                        leg['parlamentares'].append(p)

                legislaturas.append(leg)

            context['legislaturas'] = legislaturas

        return context


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
    template_name = 'crud/form.html'
    form_class = forms.ClasseForm
    model = Classe

    def form_valid(self, form):

        self.object = form.save(commit=False)

        self.object.owner = self.request.user

        if self.parent:
            self.object.parent = self.parent

        response = super(ClasseCreateView, self).form_valid(form)

        # Revisao.gerar_revisao(self.object, self.request.user)
        """if self.object.visibilidade == Classe.STATUS_PUBLIC:
            parents = self.object.parents
            for p in parents:
                p.visibilidade = Classe.STATUS_PUBLIC
                p.save()
                # Revisao.gerar_revisao(p, self.request.user)"""

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
    template_name = 'crud/form.html'
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


class PermissionsUserClasseCrud(MasterDetailCrud):
    model = PermissionsUserClasse
    parent_field = 'classe'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = [
            ('user__id', 'user', 'user__email', 'permission')]

        def get_context_data(self, **kwargs):

            ctxt = MasterDetailCrud.BaseMixin.get_context_data(self, **kwargs)

            if 'pk' in self.kwargs:
                ctxt['subnav_template_name'] = 'sigad/subnav_classe.yaml'

            return ctxt


class DocumentoCreateView(
        PermissionRequiredMixin,
        CreateView):
    permission_required = ('sigad.add_documento')
    template_name = 'crud/form.html'
    form_class = DocumentoForm
    model = Documento

    def get_success_url(self):
        return reverse_lazy(
            'cmj.sigad:documento_edit',
            kwargs={'pk': self.object.id})

    def get_form(self, form_class=None):
        form = super().get_form(self.form_class)
        form.instance.classe = Classe.objects.get(pk=self.kwargs['pk'])
        form.instance.owner = self.request.user
        return form

    def title(self):
        classe = Classe.objects.get(pk=self.kwargs['pk'])
        return classe


class DocumentoPermissionRequiredMixin(PermissionRequiredMixin):

    def has_permission(self):
        self.object = self.get_object()
        has_permission = True
        if self.object and isinstance(self.object, Documento):

            if not self.object.tipo in Documento.TDs:
                raise Http404()

            if not self.request.user.is_superuser:

                # se documento é privado e usuário que acessa não é o dono
                # não terá permissão.
                if self.object.visibilidade == Documento.STATUS_PRIVATE and \
                        self.request.user != self.object.owner:
                    has_permission = False

                # independente do status, o usuário deve ter permissão da
                # classe
                if has_permission:
                    has_permission = super().has_permission()

                # se documento é restrito, verifica se usuário possue
                # permissão para o documento
                if has_permission and \
                        self.object.visibilidade == Documento.STATUS_RESTRICT:

                    if not PermissionsUserDocumento.objects.filter(
                            documento=self.object).exists():

                        pus = self.object.classe.permissions_user_set
                        if pus.filter(
                            user__isnull=False).exists() and not pus.filter(
                                user=self.request.user).exists():
                            has_permission = False

                    else:
                        # Permissão para usuário sem associação com permission
                        qu = Q(permission__isnull=True,
                               user=self.request.user,
                               documento=self.object)

                        if PermissionsUserDocumento.objects.filter(qu).exists(
                        ) or self.request.user == self.object.owner:
                            pass
                        else:

                            perms = self.get_permission_required()

                            for perm in perms:
                                perm = perm.split('.')

                                # Permissão individual user, object, permission
                                qup = Q(
                                    permission__content_type__app_label=perm[0],
                                    permission__codename=perm[1],
                                    user=self.request.user,
                                    documento=self.object)

                                # Permissão de objeto
                                qp = Q(
                                    permission__content_type__app_label=perm[0],
                                    permission__codename=perm[1],
                                    user__isnull=True,
                                    documento=self.object)

                                # Se o objeto não possui
                                qp = Q(
                                    permission__content_type__app_label=perm[0],
                                    permission__codename=perm[1],
                                    user__isnull=True,
                                    documento=self.object)

                                if not PermissionsUserDocumento.objects.filter(
                                        qp | qup).exists():
                                    has_permission = False
                                    break
        else:
            has_permission = super().has_permission()

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

    # movido para o model documento
    """def delete_doc(self, doc):
        # transfere  midia, caso exista, para ult rev de cada descendente

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
            midia.save()"""

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete(user=request.user)
        return HttpResponseRedirect(success_url)


class DocumentoConstructView(DocumentoPermissionRequiredMixin, TemplateView):
    permission_required = ('sigad.change_documento',)
    template_name = 'sigad/documento_construct.html'
    model = Documento

    def get_object(self):
        kw = self.kwargs
        return self.model.objects.get(pk=kw.get('pk'))


class DocumentoConstructCreateView(DocumentoConstructView):
    permission_required = ('sigad.add_documento',)
    model = Classe


class DocumentoUpdateView(DocumentoPermissionRequiredMixin, UpdateView):
    permission_required = ('sigad.change_documento')
    model = Documento
    form_class = DocumentoForm
    template_name = 'sigad/documento_form.html'

    @property
    def cancel_url(self):
        return self.get_success_url()

    def get_success_url(self):
        return reverse_lazy(
            'cmj.sigad:path_view',
            kwargs={'slug': self.object.absolute_slug})

    def get_context_data(self, **kwargs):

        ctxt = UpdateView.get_context_data(self, **kwargs)
        ctxt['subnav_template_name'] = 'sigad/subnav_documento.yaml'
        return ctxt

    def form_valid(self, form):

        return UpdateView.form_valid(self, form)


class PermissionsUserDocumentoCrud(MasterDetailCrud):
    model = PermissionsUserDocumento
    parent_field = 'documento'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = [
            ('user__id', 'user', 'user__email', 'permission')]

        def get_context_data(self, **kwargs):

            ctxt = MasterDetailCrud.BaseMixin.get_context_data(self, **kwargs)

            ctxt['subnav_template_name'] = 'sigad/subnav_documento.yaml'

            return ctxt


class CaixaPublicacaoCrud(Crud):
    model = CaixaPublicacao
    help_text = 'caixapublicacao'

    class BaseMixin(Crud.BaseMixin):
        list_field_names = [
            'nome', 'key', 'documentos']

    class CreateView(Crud.CreateView):
        form_class = CaixaPublicacaoForm

    class UpdateView(Crud.UpdateView):
        form_class = CaixaPublicacaoForm

    class DetailView(Crud.DetailView):
        layout_key = 'CaixaPublicacaoDetail'
        template_name = 'sigad/caixapublicacao_detail.html'

        def get_context_data(self, **kwargs):
            context = Crud.DetailView.get_context_data(self, **kwargs)
            return context

        def get(self, request, *args, **kwargs):
            cpd_pk = request.GET.get('cpd_pk', 0)
            if cpd_pk:
                up = -1500 if 'up' in request.GET else 1500
                try:
                    cpd = CaixaPublicacaoRelationship.objects.get(pk=cpd_pk)
                    cpd.ordem += up
                    cpd.save()
                    cpd.caixapublicacao.reordene()
                except:
                    pass

            return Crud.DetailView.get(self, request, *args, **kwargs)


class CaixaPublicacaoClasseCrud(MasterDetailCrud):
    model = CaixaPublicacaoClasse
    parent_field = 'classe'

    class BaseMixin(MasterDetailCrud.BaseMixin):
        list_field_names = [
            'nome', 'key', 'classe', 'documentos']

        def get_initial(self):
            if self.object:
                classe = self.object.classe
            else:
                classe = Classe.objects.get(pk=self.kwargs.get('pk'))

            initial = MasterDetailCrud.CreateView.get_initial(self)
            initial.update({'classe': classe})
            return initial

    class CreateView(MasterDetailCrud.CreateView):
        form_class = CaixaPublicacaoForm

    class UpdateView(MasterDetailCrud.UpdateView):
        form_class = CaixaPublicacaoForm
