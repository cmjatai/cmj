from datetime import timedelta, datetime
from random import random

import dateutil.parser
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import manager
from django.db.models.aggregates import Sum
from django.db.models.deletion import PROTECT, CASCADE
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
import pytz

from cmj.mixins import CmjAuditoriaModelMixin
from sapl.utils import SaplGenericForeignKey, from_date_to_datetime_utc


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


class PullYoutubeManager(manager.Manager):

    data_min = dateutil.parser.parse('2013-11-01T00:00:00Z')

    def construct_pulls(self):

        py = self.get_queryset().last()

        if not py:
            data_base = timezone.localtime(self.data_min)
        else:
            data_base = py.published_before

        now = timezone.now()

        while data_base < now:
            td = timedelta(
                weeks=1,
                days=int(5 * random()),
                hours=int(24 * random()),
                minutes=int(60 * random()),
                seconds=int(60 * random()),
            )

            py = PullYoutube()
            py.published_after = data_base
            data_base = data_base + td
            py.published_before = data_base

            py.save()

    def pull_from_date(self, data_base=None):

        now = timezone.now()
        if not data_base:
            data_base = now
        elif not self.data_min < data_base < now:
            raise Exception(f'A data_base: {data_base} deve '
                            f'estar entre {self.data_min}  e {now}')

        pull = None
        while not pull:
            pull = self.get_queryset().filter(
                published_before__gte=data_base,
                published_after__lte=data_base
            ).first()

            if pull:
                return pull

            self.construct_pulls()


class PullYoutube(models.Model):

    objects = PullYoutubeManager()

    published_before = models.DateTimeField(verbose_name=_('published_before'))
    published_after = models.DateTimeField(verbose_name=_('published_after'))

    last_run = models.DateTimeField(
        verbose_name=_('last_run'), editable=False, auto_now=True)

    execucao = models.PositiveIntegerField(
        verbose_name=_('Execução'), default=0)

    class Meta:
        verbose_name = _('PullYoutube')
        verbose_name_plural = _("PullYoutube")
        ordering = ('id',)


class PullExecManager(manager.Manager):

    def timedelta_quota_pull(self):
        qs = self.get_queryset()

        pacific_timezone = pytz.timezone('US/Pacific')
        pacific_time = timezone.localtime(timezone=pacific_timezone)

        st = datetime.combine(pacific_time, datetime.min.time())
        st = pacific_timezone.localize(st)

        et = st + timedelta(hours=24)

        if pacific_time.hour > 17:
            st = st + timedelta(days=1)
            return st - pacific_time + timedelta(hours=150)

        interval = st, et

        qu = qs.filter(
            data_exec__gte=interval[0],
            data_exec__lt=interval[1]
        ).aggregate(Sum('quota'))

        if isinstance(qu, dict) and 'quota__sum' in qu:
            qu = qu['quota__sum'] or 0
        else:
            qu = 0

        seconds_final_day = (interval[1] - pacific_time).seconds

        chamada_livre = (9000 - qu) / 100

        if chamada_livre < 1 or seconds_final_day < 1800:
            return interval[1] - pacific_time + timedelta(minutes=150)

        week = pacific_time.weekday()
        maxs = 1800 if chamada_livre < 50 else 600
        if week in (5, 6):
            maxs = 3600
        seconds_entre_chamadas = max(
            seconds_final_day / chamada_livre,
            maxs
        )

        return timedelta(seconds=seconds_entre_chamadas)


class PullExec(models.Model):
    objects = PullExecManager()

    pull = models.ForeignKey(
        PullYoutube, verbose_name=_('PullYoutube'),
        related_name='pullyoutube_set',
        on_delete=CASCADE)

    data_exec = models.DateTimeField(
        verbose_name=_('data_exec'), editable=False, auto_now_add=True)

    quota = models.PositiveIntegerField(
        verbose_name=_('Quota'), default=1)

    class Meta:
        verbose_name = _('PullExec')
        verbose_name_plural = _("PullExec")
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
