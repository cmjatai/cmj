from django.contrib.postgres.fields.jsonb import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import ugettext_lazy as _

from cmj.mixins import CmjAuditoriaModelMixin


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

    class Meta:
        verbose_name = _('Vídeo')
        verbose_name_plural = _("Vídeos")
        ordering = ('titulo',)

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
