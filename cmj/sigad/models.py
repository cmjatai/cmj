import io
import os
import zipfile

from PIL import Image
from PIL.Image import LANCZOS
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import Q, F
from django.http.response import HttpResponse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.json import JSONField
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfgen.pdfimages import PDFImage
from reportlab.platypus.doctemplate import SimpleDocTemplate
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Parlamentar

from cmj import globalrules
from cmj.utils import get_settings_auth_user_model, YES_NO_CHOICES, CmjChoices,\
    restringe_tipos_de_arquivo_midias, TIPOS_IMG_PERMITIDOS


CLASSE_ESTRUTURAL = 0
CLASSE_DOCUMENTAL = 1
CLASSE_MISTA = 2

PERFIL_CLASSE = ((
    CLASSE_ESTRUTURAL, _('Classe Estrutural')),
    (
    CLASSE_DOCUMENTAL, _('Classe de Conteúdo')),
    (
    CLASSE_MISTA, _('Classe Mista'))
)

DOC_TEMPLATES_CHOICE_FILES = {
    1: {
        'template_name': 'path/path_documento.html',
        'create_url': 'cmj.sigad:documento_construct_create'
    },
    2:  {
        'template_name': 'path/path_thumbnails.html',
        'create_url': 'cmj.sigad:documento_construct_create'
    },
    99:  {
        'template_name': 'path/path_documento.html',
        'create_url': 'cmj.sigad:documento_construct_create'
    },
}

DOC_TEMPLATES_CHOICE = CmjChoices(
    (1, 'noticia', _('Notícia Pública')),
    (2, 'galeria', _('Galeria de Imagens')),
)


CLASSE_TEMPLATES_CHOICE_FILES = {
    1: 'path/path_classe.html',
    2: 'path/path_galeria.html',
    3: 'path/path_parlamentares.html',
    4: 'path/path_parlamentar.html',
    5: 'path/path_galeria.html',
    6: 'path/path_classe.html',
    7: 'path/path_galeria_video.html',
    99: 'path/path_documento.html',
}


CLASSE_DOC_MANAGER_CHOICE = {
    1: 'qs_news',
    2: 'view_public_gallery',
    3: 'qs_news',
    4: 'qs_news',
    5: 'qs_bi',
    6: 'qs_audio_news',
    7: 'qs_video_news',
    99: None,
}


CLASSE_TEMPLATES_CHOICE = CmjChoices(
    (1, 'lista_em_linha', _('Listagem em Linha')),
    (2, 'galeria', _('Galeria Albuns')),
    (3, 'parlamentares', _('Página dos Parlamentares')),
    (4, 'parlamentar', _('Página individual de Parlamentar')),
    (5, 'fotografia', _('Banco de Imagens')),
    (6, 'galeria_audio', _('Galeria de Áudios')),
    (7, 'galeria_video', _('Galeria de Vídeos')),
    (99, 'documento_especifico', _('Documento Específico')),
)


class Parent(models.Model):

    parent = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='childs',
        verbose_name=_('Filhos'))

    raiz = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='nodes',
        verbose_name=_('Containers'))

    related_classes = models.ManyToManyField(
        'self', blank=True,
        verbose_name=_('Classes Relacionadas'))

    class Meta:
        abstract = True

    @property
    def parents(self):
        if not self.parent:
            return []

        parents = self.parent.parents + [self.parent, ]
        return parents

    @property
    def parents_and_me(self):
        if not self.parent:
            return [self]

        parents = self.parent.parents + [self.parent, self]
        return parents

    def tree2list(self):
        yield self
        for child in self.childs.view_childs():
            for item in child.tree2list():
                yield item


class Revisao(models.Model):

    STATUS_PRIVATE = 99
    STATUS_RESTRICT_PERMISSION = 2
    STATUS_RESTRICT_USER = 1
    STATUS_PUBLIC = 0

    VISIBILIDADE_STATUS = (
        (STATUS_RESTRICT_PERMISSION, _('Restrição por Permissão')),
        (STATUS_RESTRICT_USER, _('Restrição por Usuário')),
        (STATUS_PRIVATE, _('Privado')),
        (STATUS_PUBLIC, _('Público')),
    )

    data = models.DateTimeField(
        verbose_name=_('created'),
        editable=False, auto_now_add=True)
    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('user'), related_name='+')

    json = JSONField(verbose_name=_('Json'))

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    visibilidade = models.IntegerField(
        _('Visibilidade'),
        choices=VISIBILIDADE_STATUS,
        blank=True, null=True, default=None)

    class Meta:
        ordering = ('-data',)
        verbose_name = _('Revisão')
        verbose_name_plural = _('Revisões')

    @classmethod
    def gerar_revisao(cls, instance_model, user):
        revisao = Revisao()

        if user:
            revisao.user = user
        else:
            revisao.user_id = 1  # FIXME: necessário para execuções manual...
            # resolver no model

        revisao.content_object = instance_model
        revisao.json = serializers.serialize("json", (instance_model,))

        if hasattr(instance_model, 'visibilidade'):
            revisao.visibilidade = instance_model.visibilidade

        revisao.save()
        return revisao


class CMSMixin(models.Model):

    STATUS_PRIVATE = 99
    STATUS_RESTRICT = 1
    STATUS_PUBLIC = 0

    VISIBILIDADE_STATUS = CmjChoices(
        (STATUS_RESTRICT, 'status_restrict', _('Restrito')),
        (STATUS_PUBLIC, 'status_public', _('Público')),
        (STATUS_PRIVATE, 'status_private', _('Privado')),
    )

    ALINHAMENTO_LEFT = 0
    ALINHAMENTO_JUSTIFY = 1
    ALINHAMENTO_RIGHT = 2
    ALINHAMENTO_CENTER = 3

    alinhamento_choice = CmjChoices(
        (ALINHAMENTO_LEFT, 'alinhamento_left', _('Alinhamento Esquerdo')),
        (ALINHAMENTO_JUSTIFY, 'alinhamento_justify', _('Alinhamento Completo')),
        (ALINHAMENTO_RIGHT, 'alinhamento_right', _('Alinhamento Direito')),
        (ALINHAMENTO_CENTER, 'alinhamento_center', _('Alinhamento Centralizado')),
    )

    TD_NEWS = 0
    TD_DOC = 5
    TD_BI = 10
    TD_GALERIA_PUBLICA = 20
    TD_AUDIO_NEWS = 30
    TD_VIDEO_NEWS = 40

    TPD_TEXTO = 100
    TPD_FILE = 200
    TPD_CONTAINER_SIMPLES = 700
    TPD_CONTAINER_EXTENDIDO = 701
    TPD_CONTAINER_FILE = 750
    TPD_VIDEO = 800
    TPD_AUDIO = 850
    TPD_IMAGE = 900
    TPD_GALLERY = 901

    # Documentos completos
    TDs = (TD_NEWS, TD_DOC, TD_BI, TD_GALERIA_PUBLICA,
           TD_AUDIO_NEWS, TD_VIDEO_NEWS)

    # Containers
    TDc = (TPD_CONTAINER_SIMPLES, TPD_CONTAINER_EXTENDIDO, TPD_CONTAINER_FILE)

    # Partes
    TDp = (TPD_TEXTO, TPD_FILE, TPD_VIDEO, TPD_AUDIO, TPD_IMAGE, TPD_GALLERY)

    # Tipos não acessiveis diretamente via URL
    TDp_exclude_render = (TPD_TEXTO,
                          TPD_CONTAINER_SIMPLES,
                          TPD_CONTAINER_EXTENDIDO,
                          TPD_VIDEO,
                          TPD_AUDIO)

    tipo_parte_doc = {
        'documentos': CmjChoices(
            (TD_NEWS, 'td_news', _('Notícia')),
            (TD_DOC, 'td_doc', _('Documento')),
            (TD_BI, 'td_bi', _('Banco de Imagem')),
            (TD_GALERIA_PUBLICA, 'td_galeria_publica', _('Galeria Pública')),
            (TD_AUDIO_NEWS, 'td_audio_news', _('Áudio Notícia')),
            (TD_VIDEO_NEWS, 'td_video_news', _('Vídeo Notícia')),
        ),

        'containers': CmjChoices(
            (TPD_CONTAINER_SIMPLES,
             'container', _('Container Simples')),
            (TPD_CONTAINER_EXTENDIDO,
             'container_fluid', _('Container Extendido')),
            (TPD_CONTAINER_FILE,
             'container_file', _('Container de Imagens para Arquivo PDF')),
        ),

        'subtipos': CmjChoices(
            (TPD_TEXTO, 'tpd_texto', _('Texto')),
            (TPD_FILE, 'tpd_file', _('Arquivo')),
            (TPD_VIDEO, 'tpd_video', _('Vídeo')),
            (TPD_AUDIO, 'tpd_audio', _('Áudio')),
            (TPD_IMAGE, 'tpd_image', _('Imagem')),
            (TPD_GALLERY, 'tpd_gallery',  _('Galeria de Imagens')),

        )
    }

    tipo_parte_doc_choice = (tipo_parte_doc['documentos'] +
                             tipo_parte_doc['containers'] +
                             tipo_parte_doc['subtipos'])

    created = models.DateTimeField(
        verbose_name=_('created'), editable=False, auto_now_add=True)

    public_date = models.DateTimeField(
        null=True, default=None,
        verbose_name=_('Data de Início de Publicação'))

    public_end_date = models.DateTimeField(
        null=True, default=None,
        verbose_name=_('Data de Fim de Publicação'))

    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('owner'), related_name='+')

    descricao = models.TextField(
        verbose_name=_('Descrição'),
        blank=True, null=True, default=None)

    autor = models.TextField(
        verbose_name=_('Autor'),
        blank=True, null=True, default=None)

    visibilidade = models.IntegerField(
        _('Visibilidade'),
        choices=VISIBILIDADE_STATUS,
        default=STATUS_PRIVATE)

    listar = models.BooleanField(
        _('Aparecer nas Listagens'),
        choices=YES_NO_CHOICES,
        default=True)

    class Meta:
        abstract = True

    @property
    def revisoes(self):
        # implementado como property, e não como GR, devido a necessidade
        # de manter a Revisão se o Documento for excluido.
        concret_model = None
        for kls in reversed(self.__class__.__mro__):
            if issubclass(kls, CMSMixin) and not kls._meta.abstract:
                concret_model = kls
        qs = Revisao.objects.filter(
            content_type=ContentType.objects.get_for_model(concret_model),
            object_id=self.pk)
        return qs

    def clean(self):
        """
        Check for instances with null values in unique_together fields.
        """
        from django.core.exceptions import ValidationError

        super(CMSMixin, self).clean()

        for field_tuple in self._meta.unique_together[:]:
            unique_filter = {}
            unique_fields = []
            null_found = False
            for field_name in field_tuple:
                field_value = getattr(self, field_name)
                if getattr(self, field_name) is None:
                    unique_filter['%s__isnull' % field_name] = True
                    null_found = True
                else:
                    unique_filter['%s' % field_name] = field_value
                    unique_fields.append(field_name)
            if null_found:
                unique_queryset = self.__class__.objects.filter(
                    **unique_filter)
                if self.pk:
                    unique_queryset = unique_queryset.exclude(pk=self.pk)
                if unique_queryset.exists():
                    msg = self.unique_error_message(
                        self.__class__, tuple(unique_fields))
                    raise ValidationError(msg)


class Slugged(Parent):
    titulo = models.CharField(
        verbose_name=_('Título'),
        max_length=250,
        blank=True, null=True, default='')

    slug = models.SlugField(max_length=2000)

    class Meta:
        abstract = True

    def _local_save(self, *args, **kwargs):
        super(Slugged, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):

        slug_old = self.slug
        if not self.id:
            super(Slugged, self).save(*args, **kwargs)

        kwargs['force_insert'] = False
        kwargs['force_update'] = True

        if self._meta.model == Documento and not self.parent and self.titulo:
            slug = self.titulo
        elif self._meta.model == Classe:
            slug = self.titulo
        else:
            slug = str(self.id)

        self.slug = self.generate_unique_slug(slug)
        if self.slug != slug_old:
            self.url_short = ''

        if self.parent and hasattr(self, 'classe'):
            self.visibilidade = self.parent.visibilidade
            self.public_date = self.parent.public_date
            self.listar = self.parent.listar

            if hasattr(self, 'classe'):
                self.classe = self.parent.classe

            self.raiz = self.parent.raiz if self.parent.raiz else self.parent

        super(Slugged, self).save(*args, **kwargs)

        if self._meta.model == Classe and self.slug != slug_old:
            count = self.documento_set.filter(parent__isnull=True).count()
            for documento in self.documento_set.filter(parent__isnull=True):
                documento.save()
                #print(self.titulo, count, self.slug)
                count -= 1

        for child in self.childs.all():
            child.save()

        if hasattr(self, 'cita'):
            for citacao in self.cita.all():
                citacao.save()

    def generate_unique_slug(self, slug):
        concret_model = None
        for kls in reversed(self.__class__.__mro__):
            if issubclass(kls, Slugged) and not kls._meta.abstract:
                concret_model = kls

        slug = slugify(slug)

        parents_slug = (self.parent.slug + '/') if self.parent else ''

        custom_slug = ''
        if not self.parent and hasattr(self, 'classe'):
            custom_slug = self.classe.slug + '/'
        elif hasattr(self, 'referente'):
            custom_slug = self.referente.slug + '/'

        slug_base = custom_slug + parents_slug + slug
        slug = slug_base

        i = 0
        while True:
            if i > 0:
                slug = "%s-%s" % (slug_base, i)

            try:
                obj = concret_model.objects.get(
                    #    **{'slug': slug, 'parent': self.parent})
                    **{'slug': slug})
                if obj == self:
                    raise ObjectDoesNotExist

            except ObjectDoesNotExist:
                break
            i += 1

        return slug

    @cached_property
    def nivel(self):
        parents = self.parents
        return len(parents)

    @property
    def strparents(self):
        if not self.parent:
            return []

        parents = self.parent.strparents + [self.parent.titulo, ]
        return parents

    def __str__(self):
        parents = self.strparents
        parents.append(self.titulo)

        return ':'.join(parents)

    @property
    def absolute_slug(self):
        raise NotImplementedError(_('Método não implementado pela subclasse!'))

# short_service = build(
#    'urlshortener', 'v1', developerKey=settings.GOOGLE_URL_SHORTENER_KEY)


def short_url(**kwargs):

    return ''

    # GOOGLE FOI DESATIVADO EM 30/05/2019
    import urllib3
    import json

    domain = kwargs.get('domain', 'https://www.jatai.go.leg.br')

    slug = kwargs.get('slug', '')

    fields = {
        'longUrl': '%s/%s' % (domain, slug),
    }

    encoded_data = json.dumps(fields).encode('utf-8')

    http = urllib3.PoolManager()
    r = http.request(
        'POST',
        'https://www.googleapis.com/urlshortener/v1/url?'
        'fields=id&key=' + settings.GOOGLE_URL_SHORTENER_KEY,
        body=encoded_data,
        headers={'Content-Type': 'application/json'})

    try:
        data = r.data.decode('utf-8')
        jdata = json.loads(data)

        return jdata['id']
    except Exception as e:
        print(e)
        return ''


class ShortUrl(Slugged):

    url_short = models.TextField(
        verbose_name=_('Link Curto'),
        blank=True, null=True, default=None)

    def short_url(self, sufix=None):
        if self.url_short:
            return 'https://jatai.go.leg.br/j' + self.url_short

        slug = self.absolute_slug + (sufix if sufix else '')

        bts = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

        def b62encode(id):
            if id < 62:
                return bts[id]
            r = id % 62
            return bts[r] + b62encode(id // 62)

        # if not settings.DEBUG:
        self.url_short = b62encode(self.id)
        self.save()
        return 'https://jatai.go.leg.br/j' + self.url_short

    class Meta:
        abstract = True


class Classe(ShortUrl, CMSMixin):

    codigo = models.PositiveIntegerField(verbose_name=_('Código'), default=0)

    perfil = models.IntegerField(
        _('Perfil da Classe'),
        choices=PERFIL_CLASSE,
        default=CLASSE_ESTRUTURAL)

    template_doc_padrao = models.IntegerField(
        _('Template para o Documento'),
        choices=DOC_TEMPLATES_CHOICE,
        default=DOC_TEMPLATES_CHOICE.noticia)

    tipo_doc_padrao = models.IntegerField(
        _('Tipo Padrão para Documentos desta Classe'),
        choices=CMSMixin.tipo_parte_doc['documentos'],
        default=CMSMixin.TD_DOC)

    template_classe = models.IntegerField(
        _('Template para a Classe'),
        choices=CLASSE_TEMPLATES_CHOICE,
        default=CLASSE_TEMPLATES_CHOICE.lista_em_linha)

    parlamentar = models.ForeignKey(
        Parlamentar, related_name='classe_set',
        verbose_name=_('Parlamentar'),
        blank=True, null=True, default=None)

    capa = models.OneToOneField(
        'Documento',
        blank=True, null=True, default=None,
        verbose_name=_('Capa da Classe'),
        related_name='capa')

    class Meta:
        ordering = ('codigo', '-public_date',)

        unique_together = (
            ('slug', 'parent', ),
        )
        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')
        permissions = (
            ('view_subclasse', _('Visualização de Subclasses')),
            ('view_pathclasse', _('Visualização de Classe via Path')),
        )

    def imagem_representativa(self):
        if hasattr(self, 'parlamentar'):
            return self.parlamentar
        return None

    def imagem_representativa_metatags(self):
        if hasattr(self, 'parlamentar'):
            return self.parlamentar
        return None

    @cached_property
    def conta(self):
        ct = [str(p.codigo) for p in self.parents]
        ct.append(str(self.codigo))
        if len(ct[0]) < 3:
            ct[0] = '{:03,d}'.format(int(ct[0]))
        return '.'.join(ct)

    @property
    def absolute_slug(self):
        return self.slug


class PermissionsUserClasse(CMSMixin):
    user = models.ForeignKey(get_settings_auth_user_model(),
                             blank=True, null=True, default=None,
                             verbose_name=_('Usuário'))
    classe = models.ForeignKey(Classe, verbose_name=_('Classe'),
                               related_name='permissions_user_set')
    permission = models.ForeignKey(Permission,
                                   blank=True, null=True, default=None,
                                   verbose_name=_('Permissão'))

    def __str__(self):
        return '%s - %s' % (self.permission, self.user or '')

    def validate_unique(self, exclude=None):
        if 'classe' in exclude:
            exclude.remove('classe')
        CMSMixin.validate_unique(self, exclude=exclude)

    class Meta:
        unique_together = (
            ('user', 'classe', 'permission'),
        )
        verbose_name = _('Permissão de Usuário para Classe')
        verbose_name_plural = _('Permissões de Usuários para Classes')


class DocumentoManager(models.Manager):
    use_for_related_fields = True

    filters_created = False

    def q_filters(self):
        self.q_doc_public = (Q(public_end_date__gte=timezone.now()) |
                             Q(public_end_date__isnull=True) &
                             Q(public_date__lte=timezone.now(),
                               visibilidade=Documento.STATUS_PUBLIC))
        if self.filters_created:
            return
        self.filters_created = True

        self.q_news = Q(tipo=Documento.TD_NEWS, parent__isnull=True)
        self.q_doc = Q(tipo=Documento.TD_DOC, parent__isnull=True)
        self.q_gallery = Q(tipo=Documento.TPD_GALLERY)
        self.q_image = Q(tipo=Documento.TPD_IMAGE)
        self.q_bi = Q(tipo=Documento.TD_BI, parent__isnull=True)
        self.q_audio_news = Q(
            tipo=Documento.TD_AUDIO_NEWS, parent__isnull=True)
        self.q_video_news = Q(
            tipo=Documento.TD_VIDEO_NEWS, parent__isnull=True)

    def filter_q_private(self, user):
        return Q(visibilidade=Documento.STATUS_PRIVATE, owner=user)

    def filter_q_restrict(self, user):

        qstatus = Q(visibilidade=Documento.STATUS_RESTRICT)

        # Itens restritos que possuem usuário catalogados para o acesso
        # e não dependem de permissões
        q0 = Q(permissions_user_set__permission__isnull=True,
               permissions_user_set__user=user)

        # se não existir restrição, basta pertencer ao grupo de view restrito
        q1 = Q(permissions_user_set__isnull=True)

        q2 = Q(classe__permissions_user_set__permission__isnull=True,
               classe__permissions_user_set__user=user)

        q3 = Q(classe__permissions_user_set__isnull=True)

        q4 = Q(permissions_user_set__user__isnull=True,
               permissions_user_set__permission__isnull=False)
        q5 = Q(classe__permissions_user_set__user__isnull=True,
               classe__permissions_user_set__permission__isnull=False)

        if type.mro(type(self))[0] == DocumentoManager:
            return qstatus & (q0 | q1)

        if isinstance(self.instance, Classe):
            return qstatus & (q0 | (q1 & q3) | q2 | q3 | q4 | q5)

        elif isinstance(self.instance, Parlamentar):
            return qstatus & q0
        elif isinstance(self.instance, Documento):
            return qstatus
        else:
            raise Exception(_('Modelo não tratado na filtragem de um '
                              'Documento restrito'))

    def filter_q_restrict_teste_com_permissoes(self, user):

        qstatus = Q(visibilidade=Documento.STATUS_RESTRICT)

        # Itens restritos que possuem usuário catalogados para o acesso
        # e não dependem de permissões
        q0 = Q(permissions_user_set__permission__isnull=True,
               permissions_user_set__user=user)

        # Itens restritos que não possuem usuário catalogados para o acesso
        # mas exigem que o usuário possua certas permissões
        q1 = Q(
            permissions_user_set__permission__group_set__name=globalrules.GROUP_SIGAD_VIEW_STATUS_RESTRITOS,
            permissions_user_set__user__isnull=True)

        if type.mro(type(self))[0] == DocumentoManager:
            # TODO: existe a possibilidade de isolar funcionalidades
            # Q(owner=user) por exemplo um usuário poderia cadastrar um
            # documento como restritoe, posteriormente um usuário de mais alto
            # nível retirar a visualização deste que cadastrou adicionando
            # apenas aqueles que podem ver.

            # FIXME - se o documento é restrito e a consulta não é através de
            # um RelatedManager e não possue regra explicita,
            # o "q" abaixo não fez consultas nos pais como é feito
            # individalmente na PathView em _pre_dispatch. PROJETAR como buscar
            # regras gerais definidas nos pais, seja para usuários ou para
            # permissões.
            return qstatus & (q0 | q1)

        if isinstance(self.instance, Classe):
            parent = self.instance

            q2 = Q(classe__permissions_user_set__permission__isnull=True,
                   classe__permissions_user_set__user=user)

            q3 = Q(
                classe__permissions_user_set__permission__group_set__name=globalrules.GROUP_SIGAD_VIEW_STATUS_RESTRITOS,
                classe__permissions_user_set__user__isnull=True)

            return (qstatus & (q0 | q1)) | (qstatus & (q2 | q3))

        elif isinstance(self.instance, Parlamentar):
            return qstatus & (q0 | q1)
        elif isinstance(self.instance, Documento):
            pass
        else:
            raise Exception(_('Modelo não tratado na filtragem de um '
                              'Documento restrito'))

    def view_childs(self):
        qs = self.get_queryset()
        return qs.order_by('ordem')

    def qs_bi(self, user=None):
        self.q_filters()
        return self.qs_docs(user, q_filter=self.q_bi)

    def qs_images(self, user=None):
        self.q_filters()
        return self.qs_docs(user, q_filter=self.q_image)

    def qs_news(self, user=None):
        self.q_filters()
        return self.qs_docs(user, q_filter=self.q_news)

    def qs_audio_news(self, user=None):
        self.q_filters()
        return self.qs_docs(user, q_filter=self.q_audio_news)

    def qs_video_news(self, user=None):
        self.q_filters()
        return self.qs_docs(user, q_filter=self.q_video_news)

    def all_docs(self):
        qs = self.get_queryset()
        return qs.filter(parent__isnull=True)

    def qs_docs(self, user=None, q_filter=None):

        if not q_filter:
            self.q_filters()
            q_filter = self.q_doc

        qs = self.get_queryset()

        qs = qs.filter(q_filter, self.q_doc_public)

        if user and not user.is_anonymous():
            # FIXME: manter condição apenas enquanto estiver desenvolvendo
            if user.is_superuser:
                qs_user = self.get_queryset()
                qs_user = qs_user.filter(
                    Q(visibilidade=Documento.STATUS_PRIVATE) |
                    Q(visibilidade=Documento.STATUS_RESTRICT),
                    q_filter
                )
            else:
                qs_user = self.get_queryset()
                q = self.filter_q_private(user)

                if user.groups.filter(
                    name=globalrules.GROUP_SIGAD_VIEW_STATUS_RESTRITOS
                ).exists():
                    q = q | self.filter_q_restrict(user)

                qs_user = qs_user.filter(q, q_filter)
                # print(str(qs_user.query))

            qs = qs.union(qs_user)
        else:
            qs = qs.filter(listar=True)

        qs = qs.order_by('-public_date', '-created')
        return qs

    def view_public_gallery(self):
        qs = self.get_queryset()

        qs = qs.filter(
            Q(parent__parent__public_end_date__gte=timezone.now()) |
            Q(parent__parent__public_end_date__isnull=True),
            parent__parent__public_date__lte=timezone.now(),
            parent__parent__visibilidade=Documento.STATUS_PUBLIC,
            listar=True,
            tipo=Documento.TPD_GALLERY
        ).order_by('-parent__parent__public_date')
        return qs

    def count_images(self):
        qs = self.get_queryset()
        return qs.filter(tipo=Documento.TPD_IMAGE).count()

    def create_space(self, parent, ordem, exclude=None):
        qs = self.get_queryset()

        qs = qs.filter(parent_id=parent, ordem__gte=ordem)

        if exclude:
            qs = qs.exclude(id=exclude.id)

        qs = qs.update(ordem=F('ordem') + 1)

        return qs

    def remove_space(self, parent, ordem, exclude=None):
        qs = self.get_queryset()

        qs = qs.filter(parent=parent, ordem__gte=ordem)

        if exclude:
            qs = qs.exclude(id=exclude.id)

        qs = qs.update(ordem=F('ordem') - 1)

        return qs


class Documento(ShortUrl, CMSMixin):
    objects = DocumentoManager()

    texto = models.TextField(
        verbose_name=_('Texto'),
        blank=True, null=True, default=None)

    old_path = models.TextField(
        verbose_name=_('Path no Portal Modelo 1.0'),
        blank=True, null=True, default=None)
    old_json = models.TextField(
        verbose_name=_('Json no Portal Modelo 1.0'),
        blank=True, null=True, default=None)

    extra_data = JSONField(verbose_name=_('Dados Extras'),
                           blank=True, null=True, default=None)

    parlamentares = models.ManyToManyField(
        Parlamentar, related_name='documento_set',
        verbose_name=_('Parlamentares'))

    materias = models.ManyToManyField(
        MateriaLegislativa, related_name='documento_set',
        verbose_name=_('Matérias Relacionadas'))

    classe = models.ForeignKey(
        Classe,
        related_name='documento_set',
        verbose_name=_('Classes'),
        blank=True, null=True, default=None)

    tipo = models.IntegerField(
        _('Tipo da Parte do Documento'),
        choices=CMSMixin.tipo_parte_doc_choice,
        default=CMSMixin.TD_DOC)

    template_doc = models.IntegerField(
        _('Template para o Documento'),
        choices=DOC_TEMPLATES_CHOICE,
        blank=True, null=True, default=None)

    # Possui ordem de renderização se não é uma parte de documento
    ordem = models.IntegerField(
        _('Ordem de Renderização'), default=0)

    alinhamento = models.IntegerField(
        _('Alinhamento'),
        choices=CMSMixin.alinhamento_choice,
        default=CMSMixin.ALINHAMENTO_LEFT)

    documentos_citados = models.ManyToManyField(
        'self',
        through='ReferenciaEntreDocumentos',
        through_fields=('referente', 'referenciado'),
        symmetrical=False,)

    class Meta:
        ordering = ('public_date', )
        verbose_name = _('Documento')
        verbose_name_plural = _('Documentos')
        permissions = (
            ('view_documento', _('Visualização dos Metadados do Documento.')),
            ('view_documento_media',
             _('Visualização das mídias do Documento')),
        )

    def __str__(self):
        return self.titulo or self.get_tipo_display()

    def is_parte_de_documento(self):
        return self.tipo >= 100

    @property
    def absolute_slug(self):
        return self.slug
        # return '%s/%s' % (self.classe.slug, self.slug)

    def imagem_representativa(self):

        if self.tipo == Documento.TPD_IMAGE:
            return self

        elif self.tipo == Documento.TPD_GALLERY:
            citado = self.cita.first()
            return citado

        img = self.nodes.view_childs().filter(tipo=Documento.TPD_IMAGE).first()

        if img:
            return img

        galeria = self.nodes.view_childs().filter(tipo=Documento.TPD_GALLERY).first()
        if galeria:
            img = galeria.cita.first()
            return img

        return None

    def imagem_representativa_metatags(self):
        img = self.imagem_representativa()

        if img:
            return img

        if not self.parlamentares.exists():
            return None

        return self.parlamentares.first()

    def short_url(self):
        return super().short_url(
            sufix='.page'
            if self.tipo == Documento.TPD_IMAGE else None)

    def url_prefixo_parlamentar(self):
        if self.parlamentares.count() != 1:
            return ''

        p = self.parlamentares.first()

        c = p.classe_set.first()

        if not c:
            return ''

        return c.absolute_slug

    def delete(self, using=None, keep_parents=False, user=None):
        # transfere  midia, caso exista, para ult rev de cada descendente

        childs = self.childs.view_childs()

        for child in childs:
            child.delete()

        ultima_revisao = self.revisoes.first()
        if not ultima_revisao:
            ultima_revisao = Revisao.gerar_revisao(self, user)

        if hasattr(self, 'midia'):
            midia = self.midia

            midia.documento = None
            midia.revisao = ultima_revisao
            midia.save()

        for cita in self.cita.all():
            cita.delete()

        return super().delete(using=using, keep_parents=keep_parents)

    @property
    def alinhamento_css_class(self):
        return self.alinhamento_choice.triple(self.alinhamento)

    @property
    def visibilidade_css_class(self):
        return self.VISIBILIDADE_STATUS.triple(self.visibilidade)

    @property
    def is_pdf(self):
        return self.midia.last.content_type == 'application/pdf'

    @property
    def is_pdf_container(self):

        s = set(self.childs.all().order_by(
            '-midia__versions__created').values_list(
                'midia__versions__content_type', flat=True))

        return not bool(s - TIPOS_IMG_PERMITIDOS)

    def build_container_file(self):

        s = set(self.childs.all().order_by(
            '-midia__versions__created').values_list(
                'midia__versions__content_type', flat=True))

        if not (s - TIPOS_IMG_PERMITIDOS):
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = \
                'inline; filename="documento.pdf"'

            doc = SimpleDocTemplate(
                response,
                rightMargin=0,
                leftMargin=0,
                topMargin=0,
                bottomMargin=0)

            c = canvas.Canvas(response)
            c.setTitle(self.titulo)
            A4_landscape = landscape(A4)
            for img in self.childs.order_by('ordem'):
                path = img.midia.last.file.path

                if img.midia.last.is_paisagem:
                    c.setPageSize(A4_landscape)
                else:
                    c.setPageSize(A4)

                dim = A4_landscape if img.midia.last.is_paisagem else A4
                c.drawImage(path, 0, 0,
                            width=dim[0],
                            height=dim[1])
                c.showPage()
            c.save()
            return response

        else:
            file_buffer = io.BytesIO()

            with zipfile.ZipFile(file_buffer, 'w') as file:
                for f in self.childs.order_by('ordem'):
                    fn = '%s-%s' % (
                        f.id,
                        f.midia.last.file.path.split(
                            '/')[-1])
                    file.write(f.midia.last.file.path,
                               arcname=fn)

            response = HttpResponse(file_buffer.getvalue(),
                                    content_type='application/zip')

            response['Cache-Control'] = 'no-cache'
            response['Pragma'] = 'no-cache'
            response['Expires'] = 0
            response['Content-Disposition'] = \
                'inline; filename=%s.zip' % self.raiz.slug
            return response


class ReferenciaEntreDocumentosManager(models.Manager):
    def create_space(self, referente, ordem, exclude=None):
        qs = self.get_queryset()

        qs = qs.filter(referente=referente, ordem__gte=ordem)

        if exclude:
            qs = qs.exclude(id=exclude.id)

        qs = qs.update(ordem=F('ordem') + 1)

        return qs

    def remove_space(self, referente, ordem, exclude=None):
        qs = self.get_queryset()

        qs = qs.filter(referente=referente, ordem__gte=ordem)

        if exclude:
            qs = qs.exclude(id=exclude.id)

        qs = qs.update(ordem=F('ordem') - 1)

        return qs


class ReferenciaEntreDocumentos(ShortUrl):

    objects = ReferenciaEntreDocumentosManager()
    # TODO - IMPLEMENTAR VISIBILIDADE NA REFERENCIA...
    # SIGNIFICA QUE O DOC PRIVADO PODE SER PÚBLICO POR REFERENCIA
    # TRATAR SEGURANÇA PARA QUEM REALIZAR ESSA MUDANÇA DE VISIBILIDADE
    referente = models.ForeignKey(Documento, related_name='cita',
                                  verbose_name=_('Documento Referente'),
                                  on_delete=models.PROTECT)
    referenciado = models.ForeignKey(Documento, related_name='citado_em',
                                     verbose_name=_('Documento Referenciado'),
                                     on_delete=models.CASCADE)

    descricao = models.TextField(
        verbose_name=_('Descrição'),
        blank=True, null=True, default=None)

    autor = models.TextField(
        verbose_name=_('Autor'),
        blank=True, null=True, default=None)

    # Possui ordem de renderização
    ordem = models.IntegerField(
        _('Ordem de Renderização'), default=0)

    class Meta:
        ordering = ('referente', 'ordem')

    def short_url(self):
        return super().short_url(
            sufix='.page'
            if self.referenciado.tipo == Documento.TPD_IMAGE else None)

    @property
    def parents(self):
        _self = self.referente
        if not _self.parent:
            return []

        parents = _self.parent.parents + [_self.parent, ]
        return parents

    @property
    def absolute_slug(self):
        # return '%s/%s' % (self.referente.absolute_slug, self.slug)
        return self.slug


class PermissionsUserDocumento(CMSMixin):
    user = models.ForeignKey(get_settings_auth_user_model(),
                             blank=True, null=True, default=None,
                             verbose_name=_('Usuário'))
    documento = models.ForeignKey(Documento,
                                  related_name='permissions_user_set',
                                  verbose_name=_('Documento'))
    permission = models.ForeignKey(Permission,
                                   blank=True, null=True, default=None,
                                   verbose_name=_('Permissão'))

    class Meta:
        unique_together = (
            ('user', 'documento', 'permission'),
        )
        verbose_name = _('Permissão de Usuário para Documento')
        verbose_name_plural = _('Permissões de Usuários para Documentos')


class Midia(models.Model):

    documento = models.OneToOneField(
        Documento,
        blank=True, null=True, default=None,
        verbose_name=_('Documento'),
        related_name='midia')

    revisao = models.OneToOneField(
        Revisao,
        blank=True, null=True, default=None,
        verbose_name=_('Revisão'),
        related_name='midia')

    class Meta:
        verbose_name = _('Mídia Versionada')
        verbose_name_plural = _('Mídias Versionadas')

    @cached_property
    def last(self):
        return self.versions.first()


def media_path(instance, filename):
    return './sigad/documento/%s/media/%s/%s' % (
        instance.midia.documento_id,
        instance.midia_id,
        filename)


media_protected = FileSystemStorage(
    location=settings.MEDIA_PROTECTED_ROOT, base_url='DO_NOT_USE')


class VersaoDeMidia(models.Model):
    created = models.DateTimeField(
        verbose_name=_('created'),
        editable=False, auto_now_add=True)
    owner = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('owner'), related_name='+')

    file = models.FileField(
        blank=True,
        null=True,
        storage=media_protected,
        upload_to=media_path,
        verbose_name=_('Mídia'),
        validators=[restringe_tipos_de_arquivo_midias])

    content_type = models.CharField(
        max_length=250,
        default='')

    midia = models.ForeignKey(
        Midia, verbose_name=_('Mídia Versionada'),
        related_name='versions')

    def delete(self, using=None, keep_parents=False):
        if self.file:
            self.file.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, with_file=None):
        _ret = models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update, using=using, update_fields=update_fields)

        if not with_file:
            return _ret

        mime, ext = restringe_tipos_de_arquivo_midias(with_file)

        name_file = 'midia.%s' % ext
        self.content_type = mime
        self.file.save(name_file, File(with_file))

    @cached_property
    def simple_name(self):
        return self.file.name.split('/')[-1]

    @cached_property
    def width(self):
        try:
            nf = '%s/%s' % (media_protected.location, self.file.name)
            im = Image.open(nf)
            return im.width
        except:
            return 0

    @cached_property
    def height(self):
        try:
            nf = '%s/%s' % (media_protected.location, self.file.name)
            im = Image.open(nf)
            return im.height
        except:
            return 0

    @cached_property
    def is_paisagem(self):
        return self.height < self.width

    def rotate(self, rotate):
        import os
        try:
            nf = '%s/%s' % (media_protected.location, self.file.name)
            im = Image.open(nf)
            im = im.rotate(rotate, resample=LANCZOS, expand=True)
            im.save(nf, dpi=(300, 300))
            im.close()
            dirname = os.path.dirname(self.file.path)
            for f in os.listdir(dirname):
                filename = '%s/%s' % (dirname, f)
                if filename == nf:
                    continue
                os.remove(filename)
        except Exception as e:
            pass

    def thumbnail(self, width='thumb'):
        sizes = {
            '24': (24, 24),
            '48': (48, 48),
            '96': (96, 96),
            '128': (128, 128),
            '256': (256, 256),
            '512': (512, 512),
            '768': (768, 768),
            '1024': (1024, 1024),
        }

        if width not in sizes:
            width = '96'

        nf = '%s/%s' % (media_protected.location, self.file.name)
        nft = nf.split('/')
        nft = '%s/%s.%s' % ('/'.join(nft[:-1]), width, nft[-1])

        if os.path.exists(nft):
            file = io.open(nft, 'rb')
            return file

        im = Image.open(nf)
        if sizes[width][0] >= im.width:
            file = io.open(nf, 'rb')
        else:
            if sizes[width][0] < 512:
                if im.width > im.height:
                    im.thumbnail(sizes[width])
                else:
                    size = (
                        int(sizes[width][0] * (im.width / im.height)),
                        int(sizes[width][1] * (im.width / im.height))
                    )
                    im.thumbnail(size)
            else:
                im.thumbnail(sizes[width], resample=LANCZOS)
            im.save(nft)
            im.close()
            file = io.open(nft, 'rb')

        return file

    def icon(self):
        return self.get_filename.split('.')[-1]

    class Meta:
        ordering = ('-created',)
        verbose_name = _('Mídia')
        verbose_name_plural = _('Mídias')


class CaixaPublicacao(models.Model):
    key = models.CharField(
        max_length=250,
        default='')
    nome = models.CharField(
        max_length=250,
        default='')

    classe = models.ForeignKey(
        Classe,
        related_name='caixapublicacao_set',
        verbose_name=_('Classes'),
        blank=True, null=True, default=None)

    documentos = models.ManyToManyField(
        'sigad.Documento', blank=True,
        through='CaixaPublicacaoRelationship',
        through_fields=('caixapublicacao', 'documento'),
        related_query_name='caixapublicacao_set',
        verbose_name=_('Documentos da Caixa de Públicação'),
        symmetrical=False)

    def reordene(self):
        ordem = 0
        for cpd in self.caixapublicacaorelationship_set.all():
            ordem += 1000
            cpd.ordem = ordem
            cpd.save()

    def __str__(self):
        if self.classe:
            return '%s (%s)' % (self.nome, self.classe)
        else:
            return self.nome

    class Meta:
        verbose_name = _('Caixa de Publicação')
        verbose_name_plural = _('Caixas de Publicação')


class CaixaPublicacaoClasse(CaixaPublicacao):

    class Meta:
        proxy = True
        verbose_name = _('Caixa de Publicação')
        verbose_name_plural = _('Caixas de Publicação')


class CaixaPublicacaoRelationship(models.Model):

    caixapublicacao = models.ForeignKey(
        CaixaPublicacao, on_delete=models.CASCADE)
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField(default=0)

    def __str__(self):
        return '{:02d} - {}'.format(self.ordem // 1000, self.documento)

    class Meta:
        unique_together = ('caixapublicacao', 'documento')
        ordering = ('ordem', '-documento')
        verbose_name = _('Documentos da Caixa de Publicação')
        verbose_name_plural = _('Documentos da Caixa de Publicação')
