import io
import os

from PIL import Image
from PIL.Image import NEAREST
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.json import JSONField
from googleapiclient import sample_tools
from googleapiclient.discovery import build
from oauth2client import client
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Parlamentar

from cmj.utils import get_settings_auth_user_model, CmjChoices


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
    5: 'path/path_classe.html',
}

CLASSE_TEMPLATES_CHOICE = CmjChoices(
    (1, 'lista_em_linha', _('Listagem Simples em Linha')),
    (2, 'galeria', _('Galeria Pública de Albuns')),
    (3, 'parlamentares', _('Página dos Parlamentares')),
    (4, 'parlamentar', _('Página individual de Parlamentar')),
    (5, 'fotografia', _('Banco de Imagens')),
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
        related_name='containers',
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
        blank=True, null=True, default=None)

    slug = models.SlugField(max_length=2000)

    class Meta:
        abstract = True

    def _local_save(self, *args, **kwargs):
        super(Slugged, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):
        s_old = self.slug

        if self.titulo and not self.parent or not hasattr(self, 'classe'):
            slug = self.titulo
        else:
            super(Slugged, self).save(*args, **kwargs)
            slug = str(self.id)

        self.slug = self.generate_unique_slug(slug)

        if self.id:
            kwargs['force_insert'] = False
            kwargs['force_update'] = True

        if self.parent:
            self.visibilidade = self.parent.visibilidade
            self.public_date = self.parent.public_date

            if hasattr(self, 'classe'):
                self.classe = self.parent.classe

            self.raiz = self.parent.raiz if self.parent.raiz else self.parent

        super(Slugged, self).save(*args, **kwargs)

        for child in self.childs.all():
            child.save()

    def generate_unique_slug(self, slug):
        concret_model = None
        for kls in reversed(self.__class__.__mro__):
            if issubclass(kls, Slugged) and not kls._meta.abstract:
                concret_model = kls

        slug = slugify(slug)

        parents_slug = (self.parent.slug + '/') if self.parent else ''

        i = 0
        while True:
            if i > 0:
                if i > 1:
                    slug = slug.rsplit("-", 1)[0]
                slug = "%s-%s" % (slug, i)

            try:
                obj = concret_model.objects.get(
                    #    **{'slug': slug, 'parent': self.parent})
                    **{'slug': parents_slug + slug})
                if obj == self:
                    raise ObjectDoesNotExist

            except ObjectDoesNotExist:
                break
            i += 1

        custom_slug = ''
        if not self.parent and hasattr(self, 'classe'):
            custom_slug = self.classe.slug + '/'
        elif hasattr(self, 'referente'):
            custom_slug = self.referente.slug + '/'
        slug = custom_slug + parents_slug + slug

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

    import urllib3
    import json

    domain = kwargs.get('domain', 'http://www2.camarajatai.go.gov.br')

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
            return self.url_short

        slug = self.absolute_slug + (sufix if sufix else '')

        if not settings.DEBUG:
            self.url_short = short_url(slug=slug)
            self.save()
        return self.url_short

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

    template_classe = models.IntegerField(
        _('Template para a Classe'),
        choices=CLASSE_TEMPLATES_CHOICE,
        default=CLASSE_TEMPLATES_CHOICE.lista_em_linha)

    parlamentar = models.ForeignKey(
        Parlamentar, related_name='classe_set',
        verbose_name=_('Parlamentar'),
        blank=True, null=True, default=None)

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
    permission = models.ForeignKey(Permission, verbose_name=_('Permissão'))

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
        if self.filters_created:
            return
        self.filters_created = True

        self.q_doc = Q(tipo=Documento.TD_DOC, parent__isnull=True)
        self.q_gallery = Q(tipo=Documento.TPD_GALLERY)
        self.q_image = Q(tipo=Documento.TPD_IMAGE)
        self.q_bi = Q(tipo=Documento.TD_BI, parent__isnull=True)
        self.q_doc_public = (Q(public_end_date__gte=timezone.now()) |
                             Q(public_end_date__isnull=True) &
                             Q(public_date__lte=timezone.now(),
                               visibilidade=Documento.STATUS_PUBLIC))

    def filter_q_private(self, user):
        return Q(visibilidade=Documento.STATUS_PRIVATE, owner=user)

    def filter_q_restrict(self, user):
        return ((Q(owner=user) |
                 Q(permissions_user_set__user=user,
                   permissions_user_set__permission__isnull=True)) &
                Q(visibilidade=Documento.STATUS_RESTRICT))

    def view_childs(self):
        qs = self.get_queryset()
        return qs.order_by('ordem')

    def qs_bi(self, user=None):
        self.q_filters()
        return self.qs_docs(user, q_filter=self.q_bi)

    def qs_images(self, user=None):
        self.q_filters()
        return self.qs_docs(user, q_filter=self.q_image)

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
                qs_user = qs_user.filter(
                    self.filter_q_private(user) | self.filter_q_restrict(user),
                    q_filter
                )
            qs = qs.union(qs_user)

        qs = qs.order_by('-public_date', '-created')
        return qs

    def view_public_gallery(self):
        qs = self.get_queryset()

        qs = qs.filter(
            Q(parent__parent__public_end_date__gte=timezone.now()) |
            Q(parent__parent__public_end_date__isnull=True),
            parent__parent__public_date__lte=timezone.now(),
            parent__parent__visibilidade=Documento.STATUS_PUBLIC,

            tipo=Documento.TPD_GALLERY
        ).order_by('-parent__parent__public_date')
        return qs

    def create_space(self, validated_data):
        qs = self.get_queryset()

        qs = qs.filter(parent_id=validated_data['parent'],
                       ordem__gte=validated_data['ordem']
                       ).update(ordem=F('ordem') + 1)
        return qs

    def remove_space(self, parent, ordem):
        qs = self.get_queryset()

        qs = qs.filter(parent=parent,
                       ordem__gte=ordem
                       ).update(ordem=F('ordem') - 1)
        return qs


class Documento(ShortUrl, CMSMixin):
    objects = DocumentoManager()

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

    TD_DOC = 0
    TD_BI = 10
    TD_GALERIA_PUBLICA = 20
    TPD_TEXTO = 100
    TPD_CONTAINER_SIMPLES = 700
    TPD_CONTAINER_EXTENDIDO = 701
    TPD_VIDEO = 800
    TPD_AUDIO = 850
    TPD_IMAGE = 900
    TPD_GALLERY = 901

    # Documentos completos
    TDs = (TD_DOC, TD_BI, TD_GALERIA_PUBLICA)

    # Containers
    TDc = (TPD_CONTAINER_SIMPLES, TPD_CONTAINER_EXTENDIDO)

    # Partes
    TDp = (TPD_TEXTO, TPD_VIDEO, TPD_AUDIO, TPD_IMAGE, TPD_GALLERY)

    tipo_parte_doc = {
        'documentos': CmjChoices(
            (TD_DOC, 'td_doc', _('Documento')),
            (TD_BI, 'td_bi', _('Banco de Imagem')),
            (TD_GALERIA_PUBLICA, 'td_galeria_publica', _('Galeria Pública'))
        ),

        'containers': CmjChoices(
            (TPD_CONTAINER_SIMPLES,
             'container', _('Container Simples')),
            (TPD_CONTAINER_EXTENDIDO,
             'container_fluid', _('Container Extendido')),
        ),

        'subtipos': CmjChoices(
            (TPD_TEXTO, 'tpd_texto', _('Texto')),
            (TPD_VIDEO, 'tpd_video', _('Vídeo')),
            (TPD_AUDIO, 'tpd_audio', _('Áudio')),
            (TPD_IMAGE, 'tpd_image', _('Imagem')),
            (TPD_GALLERY, 'tpd_gallery',  _('Galeria de Imagens')),

        )
    }

    tipo_parte_doc_choice = (tipo_parte_doc['documentos'] +
                             tipo_parte_doc['containers'] +
                             tipo_parte_doc['subtipos'])

    texto = models.TextField(
        verbose_name=_('Texto'),
        blank=True, null=True, default=None)

    old_path = models.TextField(
        verbose_name=_('Path no Portal Modelo 1.0'),
        blank=True, null=True, default=None)
    old_json = models.TextField(
        verbose_name=_('Json no Portal Modelo 1.0'),
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
        choices=tipo_parte_doc_choice,
        default=TD_DOC)

    template_doc = models.IntegerField(
        _('Template para o Documento'),
        choices=DOC_TEMPLATES_CHOICE,
        blank=True, null=True, default=None)

    # Possui ordem de renderização se não é uma parte de documento
    ordem = models.IntegerField(
        _('Ordem de Renderização'), default=0)

    alinhamento = models.IntegerField(
        _('Alinhamento'),
        choices=alinhamento_choice,
        default=ALINHAMENTO_LEFT)

    documentos_citados = models.ManyToManyField(
        'self',
        through='ReferenciaEntreDocumentos',
        through_fields=('referente', 'referenciado'),
        symmetrical=False,)

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

        for item in self.childs.view_childs():
            img = item.imagem_representativa()

            if img:
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

    @property
    def alinhamento_css_class(self):
        return self.alinhamento_choice.triple(self.alinhamento)

    @property
    def visibilidade_css_class(self):
        return self.VISIBILIDADE_STATUS.triple(self.visibilidade)

    class Meta:
        ordering = ('public_date', )
        verbose_name = _('Documento')
        verbose_name_plural = _('Documentos')
        permissions = (
            ('view_documento', _('Visualização dos Metadados do Documento.')),
            ('view_documento_media',
             _('Visualização das mídias do Documento')),
        )


class ReferenciaEntreDocumentos(ShortUrl):
    # TODO - IMPLEMENTAR VISIBILIDADE NA REFERENCIA...
    # SIGNIFICA QUE O DOC PRIVADO PODE SER PÚBLICO POR REFERENCIA
    # TRATAR SEGURANÇA PARA QUEM REALIZAR ESSA MUDANÇA DE VISIBILIDADE
    referente = models.ForeignKey(Documento, related_name='cita',
                                  verbose_name=_('Documento Referente'),
                                  on_delete=models.CASCADE)
    referenciado = models.ForeignKey(Documento, related_name='citado_em',
                                     verbose_name=_('Documento Referenciado'),
                                     on_delete=models.PROTECT)

    # Possui ordem de renderização
    ordem = models.IntegerField(
        _('Ordem de Renderização'), default=0)

    class Meta:
        ordering = ('referenciado', 'ordem')

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
        verbose_name=_('Mídia'))

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
                im.thumbnail(sizes[width], resample=NEAREST)
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
