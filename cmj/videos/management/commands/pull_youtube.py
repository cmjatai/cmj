
from datetime import timedelta, datetime
import json
import logging
from random import random
import re

import dateutil.parser
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q, F
from django.db.models.signals import post_delete, post_save
from django.utils import timezone

from cmj.sigad.models import Documento
from cmj.utils import Manutencao
from cmj.videos.functions import pull_youtube_metadata_video, pull_youtube,\
    vincular_sistema_aos_videos, video_documento_na_galeria
from cmj.videos.models import Video, PullYoutube, VideoParte, PullExec
import requests as rq


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):

        m = Manutencao()
        m.desativa_signals()

        self.logger = logging.getLogger(__name__)

        # PullExec.objects.timedelta_quota_pull()
        # self.corrigir_erro_causado_em_full_metadata()
        videos = Video.objects.filter(
            json__snippet__liveBroadcastContent='upcoming')
        for v in videos[:50]:
            print(v.execucao, v.created, v)
            pull_youtube_metadata_video(v)
        # pull_youtube()
        # vincular_sistema_aos_videos()
        # video_documento_na_galeria()
        return
        # vincular_sistema_aos_videos()
        # video_documento_na_galeria()
        # pull_youtube_metadata_video(Video.objects.first())

        for v in Video.objects.order_by('-id')[:40]:

            print(v.id, v)
            if v.id == 1273:
                pull_youtube_metadata_video(v)
            continue

            for vp in v.videoparte_set.all():
                d = vp.content_object

                if not d:
                    vp.delete()
                    continue

                if vp.content_type_id == 202:
                    d.delete()
                    vp.delete()

            if not v.videoparte_set.exists():
                v.delete()
                continue

        return

        # Video.objects.all().update(created=F('modified'))

        # PullYoutube.objects.pull_from_date()
        m.desativa_auto_now()

        # self.corrigir_erro_causado_em_full_metadata()
        # return

        """upcoming_or_live = Video.objects.filter(
            json__snippet__liveBroadcastContent__in=('upcoming', 'live')).exists()

        if upcoming_or_live:
            delay = timezone.now() + timedelta(seconds=10)
            task_pull_youtube.apply_async((upcoming_or_live,), eta=delay)

        return"""

        if not settings.DEBUG:
            self.pull_youtube()

        self.get_full_metadata_video()
        # return

        m.ativa_auto_now()

        self.vincular_sistema_aos_videos()

        self.video_documento_na_galeria()

    def get_full_metadata_video(self):
        videos = Video.objects.all(
        ).order_by('execucao', '-created')
        #    json__snippet__liveBroadcastContent__in=('upcoming', 'live')

        videos = videos[:100]

        #now = timezone.now()

        for v in videos:
            print(v.id, v.vid, v)
            try:
                pull_youtube_metadata_video(v)
            except:
                pass

        """upcoming_or_live = Video.objects.filter(
            json__snippet__liveBroadcastContent__in=('upcoming', 'live'))

        if upcoming_or_live.exists():
            v = upcoming_or_live.first()

            td = now - v.modified

            if td.total_seconds() > 600:
                delay = timezone.now() + timedelta(seconds=30)
                task_pull_youtube.apply_async(eta=delay)"""

    def corrigir_erro_causado_em_full_metadata(self):

        videos = Video.objects.all()

        for v in videos:

            for vp in v.videoparte_set.all():

                if isinstance(vp.content_object, Documento):
                    d = vp.content_object

                    # if d.classe_id == 233:
                    #    continue

                    for r in d.revisoes.all():
                        if not r.user:
                            continue

                        if r.user.id == 76:
                            d.titulo = r.obj[0]['fields']['titulo']
                            d.descricao = r.obj[0]['fields']['descricao']
                            d.save()
                            print(r.id, r.user.id, r.user, d.id, d)
                            break
