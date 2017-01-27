import io
import os

from PIL import Image
from PIL.Image import NEAREST
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.fields import GenericForeignKey,\
    GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.json import JSONField

from cmj import sigad
from cmj.utils import get_settings_auth_user_model


STATUS_PRIVATE = 99
STATUS_RESTRICT = 1
STATUS_PUBLIC = 0

VISIBILIDADE_STATUS = (
    (STATUS_RESTRICT, _('Restrito')),
    (STATUS_PRIVATE, _('Privado')),
    (STATUS_PUBLIC, _('Público')),
)


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


class Parent(models.Model):

    parent = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='childs',
        verbose_name=_('Filhos'))

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


class CMSMixin(models.Model):
    created = models.DateTimeField(
        verbose_name=_('created'),
        editable=False, auto_now_add=True)

    public_date = models.DateTimeField(null=True, default=None,
                                       verbose_name=_('Data de Início de Publicação'))

    public_end_date = models.DateTimeField(
        null=True, default=None,
        verbose_name=_('Data de Fim de Publicação'))

    owner = models.ForeignKey(
        get_settings_auth_user_model(), verbose_name=_('owner'), related_name='+')

    descricao = models.TextField(
        verbose_name=_('Descrição'),
        blank=True, null=True, default=None)

    visibilidade = models.IntegerField(
        _('Visibilidade'),
        choices=VISIBILIDADE_STATUS,
        default=STATUS_PRIVATE)

    class Meta:
        abstract = True

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


class Revisao(models.Model):

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

    class Meta:
        ordering = ('-data',)
        verbose_name = _('Revisão')
        verbose_name_plural = _('Revisões')

    @classmethod
    def gerar_revisao(cls, instance_model, user):
        revisao = Revisao()
        revisao.user = user
        revisao.content_object = instance_model
        revisao.json = serializers.serialize("json", (instance_model,))
        revisao.save()


class Slugged(Parent):
    titulo = models.CharField(
        verbose_name=_('Título'),
        max_length=250)

    slug = models.SlugField(max_length=2000)

    revisoes = GenericRelation(Revisao, related_query_name='revisoes')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.slug = self.generate_unique_slug()
        super(Slugged, self).save(*args, **kwargs)

    def generate_unique_slug(self):
        concret_model = None
        for kls in reversed(self.__class__.__mro__):
            if issubclass(kls, Slugged) and not kls._meta.abstract:
                concret_model = kls

        slug = slugify(self.titulo)
        parents_slug = self.parent.slug if self.parent else ''

        i = 0
        while True:
            if i > 0:
                if i > 1:
                    slug = slug.rsplit("-", 1)[0]
                slug = "%s-%s" % (slug, i)

            try:

                obj = concret_model.objects.get(
                    **{'slug': parents_slug + '/' + slug})
                if obj == self:
                    raise ObjectDoesNotExist

            except ObjectDoesNotExist:
                break
            i += 1
        return parents_slug + '/' + slug

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


class Classe(Slugged, CMSMixin):

    codigo = models.PositiveIntegerField(verbose_name=_('Código'), default=0)

    perfil = models.IntegerField(
        _('Perfil da Classe'),
        choices=PERFIL_CLASSE,
        default=CLASSE_ESTRUTURAL)

    class Meta:
        ordering = ('codigo', '-public_date',)

        unique_together = (
            ('slug', 'parent', ),
        )
        verbose_name = _('Classe')
        verbose_name_plural = _('Classes')
        permissions = (
            ('view_subclasse', _('Visualização de Subclasses')),
        )

    @cached_property
    def conta(self):
        ct = [str(p.codigo) for p in self.parents]
        ct.append(str(self.codigo))
        if len(ct[0]) < 3:
            ct[0] = '{:03,d}'.format(int(ct[0]))
        return '.'.join(ct)


class PermissionsUserClasse(CMSMixin):
    user = models.ForeignKey(
        get_settings_auth_user_model(), verbose_name=_('Usuário'))
    classe = models.ForeignKey(Classe, verbose_name=_('Classe'))
    permission = models.ForeignKey(Permission, verbose_name=_('Permissão'))

    class Meta:
        unique_together = (
            ('user', 'classe', 'permission'),
        )
        verbose_name = _('Permissão de Usuário para Classe')
        verbose_name_plural = _('Permissões de Usuários para Classes')
"""

class Documento(SigadModelMixin):

    titulo = models.CharField(
        verbose_name=_('Título'),
        max_length=250,
        blank=True, null=True, default=None)
    descricao = models.TextField(
        verbose_name=_('Descrição'),
        blank=True, null=True, default=None)
    texto = models.TextField(
        verbose_name=_('Texto'),
        blank=True, null=True, default=None)

    data_documento = models.DateTimeField(
        verbose_name=_('Data do Documento'))

    data_publicacao = models.DateField(
        blank=True, null=True, default=None,
        verbose_name=_('Data de Publicação'))
    hora_publicacao = models.TimeField(
        blank=True, null=True, default=None,
        verbose_name=_('Horário de Publicação'))

    parent = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='documentos_set',
        verbose_name=_('Documentos'))

    classe = models.ForeignKey(
        Classe,
        related_name='classes',
        verbose_name=_('Classes'))

    ''' se media_of estiver preenchido significa que a instancia
    do documento é uma midia de algum documento
    - TODO: verificar a necessidade de ser OneToOneField'''
    media_of = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='docmedias_set',
        verbose_name=_('Mídias do Documento'))

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _('Documento')
        verbose_name_plural = _('Documentos')
        permissions = (
            ('view_documento', _('Visualização dos Metadados do Documento.')),
            ('view_documento_media',
             _('Visualização das mídias do Documento')),
        )


class VersionedMedia(models.Model):

    documento = models.OneToOneField(
        Documento,
        verbose_name=_('Mídia'),
        related_name='media')

    class Meta:
        verbose_name = _('Mídia Versionada')
        verbose_name_plural = _('Mídias Versionadas')

    @cached_property
    def last(self):
        return self.versions.last()


def media_path(instance, filename):
    return './sigad/documento/%s/media/%s/%s' % (
        instance.vm.documento_id,
        instance.vm_id,
        filename)

media_protected = FileSystemStorage(
    location=settings.MEDIA_PROTECTED_ROOT, base_url='DO_NOT_USE')


class Media(models.Model):
    created = models.DateTimeField(
        verbose_name=_('created'),
        editable=False, auto_now_add=True)
    owner = models.ForeignKey(
        get_settings_auth_user_model(), verbose_name=_('owner'), related_name='+')

    file = models.FileField(
        blank=True,
        null=True,
        storage=media_protected,
        upload_to=media_path,
        verbose_name=_('Mídia'))

    content_type = models.CharField(
        max_length=250,
        default='')

    vm = models.ForeignKey(
        VersionedMedia, verbose_name=_('Mídia Versionada'),
        related_name='versions')

    @cached_property
    def simple_name(self):
        return self.file.name.split('/')[-1]

    def thumbnail(self, width=100):
        sizes = {
            'verysmall': (24, 24),
            'small': (48, 48),
            'thumb': (96, 96),
            'medium': (256, 256),
            'large': (512, 512),
            'verylarge': (768, 768),
        }
        try:
            w = int(width)
            sizes[str(width)] = w, w
            width = str(width)
        except:
            pass

        nf = '%s%s' % (media_protected.location, self.file.name[1:])
        nft = nf.split('/')
        nft = '%s/%s.%s' % ('/'.join(nft[:-1]), width, nft[-1])

        if os.path.exists(nft):
            file = io.open(nft, 'rb')
            return file

        if width not in sizes:
            width = 'thumb'

        im = Image.open(nf)
        if sizes[width][0] >= im.width:
            file = io.open(nf, 'rb')
        else:
            if sizes[width][0] < 512:
                im.thumbnail(sizes[width])
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
"""
