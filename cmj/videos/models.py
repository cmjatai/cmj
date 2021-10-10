from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT
from django.utils.translation import ugettext_lazy as _

from cmj.mixins import CmjAuditoriaModelMixin
from sapl.utils import SaplGenericForeignKey


class Video(CmjAuditoriaModelMixin):

    vid = models.CharField(
        max_length=30,
        verbose_name=_('Video Id '),
        unique=True)

    json = JSONField(
        verbose_name=_('Object'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    titulo = models.CharField(
        verbose_name=_('Título'),
        max_length=250,
        blank=True, null=True, default='')

    execucao = models.PositiveIntegerField(
        verbose_name=_('Execução'), default=0)

    class Meta:
        verbose_name = _('Vídeo')
        verbose_name_plural = _("Vídeos")
        ordering = ('-created',)

    def __str__(self):
        return self.titulo


class PullYoutube(models.Model):

    published_before = models.DateTimeField(verbose_name=_('published_before'))
    published_after = models.DateTimeField(verbose_name=_('published_after'))

    execucao = models.PositiveIntegerField(
        verbose_name=_('Execução'), default=0)

    class Meta:
        verbose_name = _('PullYoutube')
        verbose_name_plural = _("PullYoutube")
        ordering = ('id',)


class VideoParte(models.Model):

    video = models.ForeignKey(
        Video, verbose_name=_('Vídeo'),
        related_name='videoparte_set',
        on_delete=PROTECT)

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None,
        on_delete=PROTECT)

    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)

    content_object = SaplGenericForeignKey('content_type', 'object_id')

    time_start = models.PositiveIntegerField(default=0)

    fieldname = models.CharField(
        max_length=250, blank=True, null=True, default='')

    class Meta:
        verbose_name = _('VideoParte')
        verbose_name_plural = _("Video Partes")

        ordering = ('id',)
