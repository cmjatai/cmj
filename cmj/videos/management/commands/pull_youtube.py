
from datetime import timedelta, datetime
from random import random
import json
import logging
import re

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q, F
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
import dateutil.parser

from cmj.sigad.models import Documento
from cmj.signals import Manutencao
from cmj.videos.functions import pull_youtube_metadata_video
from cmj.videos.models import Video, PullYoutube, VideoParte
import requests as rq


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):

        m = Manutencao()
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        # Video.objects.all().update(created=F('modified'))
        return
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

    def vincular_sistema_aos_videos(self):

        videos = Video.objects.order_by('created')

        ct_doc = ContentType.objects.get_for_model(Documento)
        for v in videos:

            for app in apps.get_app_configs():
                if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                    continue

                if app.name not in ('cmj.sigad', 'sapl.sessao', 'sapl.materia'):
                    continue

                for m in app.get_models():
                    ct = ContentType.objects.get_for_model(m)
                    fields_name = tuple(
                        map(lambda x: x.name, m._meta.get_fields()
                            )
                    )

                    if m != Documento:
                        if 'url_video' not in fields_name:
                            continue

                    f = 'texto' if m == Documento else 'url_video'

                    p = {f'{f}__contains': v.vid}

                    for item in m.objects.filter(**p):
                        try:

                            vf = getattr(item, f)
                            i = item if m != Documento else item.raiz

                            vp = VideoParte.objects.filter(
                                video=v,
                                content_type=ct,
                                object_id=i.id
                            )

                            if vp.exists():
                                continue

                            vp = VideoParte()
                            vp.video = v
                            vp.content_object = i
                            vp.fieldname = f

                            r = re.findall(r'http.+youtu.+\?.*t=(\d+)', vf)

                            if r:
                                vp.time_start = int(r[-1])

                            vp.save()

                        except:
                            pass

    def video_documento_na_galeria(self):

        videos = Video.objects.order_by('created')

        ct_doc = ContentType.objects.get_for_model(Documento)
        for v in videos:

            vps = v.videoparte_set.filter(content_type=ct_doc)

            docs = tuple(
                filter(
                    lambda o: o.classe_id == 233,
                    map(
                        lambda vp: vp.content_object,
                        vps)
                )
            )
            if docs:
                continue

            video_dict = v.json['snippet']

            documento = Documento()
            documento.titulo = video_dict['title']
            documento.descricao = video_dict['description']
            documento.public_date = dateutil.parser.parse(
                video_dict['publishedAt'])
            documento.classe_id = 233
            documento.tipo = Documento.TD_VIDEO_NEWS
            documento.template_doc = 1
            documento.owner_id = 1
            documento.visibilidade = Documento.STATUS_PUBLIC

            documento.extra_data = v.json
            documento.save()

            documento.childs.all().delete()

            container = Documento()
            container.raiz = documento
            container.titulo = ''
            container.descricao = ''
            container.classe_id = 233
            container.tipo = Documento.TPD_CONTAINER_SIMPLES
            container.owner_id = 1
            container.parent = documento
            container.ordem = 1
            container.visibilidade = documento.visibilidade
            container.save()

            video = Documento()
            video.raiz = documento
            video.titulo = ''
            video.descricao = ''
            video.classe_id = 233
            video.tipo = Documento.TPD_VIDEO
            video.owner_id = 1
            video.parent = container
            video.ordem = 1
            video.extra_data = v.json
            video.visibilidade = documento.visibilidade

            video.texto = (
                '<iframe width="560" height="315"'
                'src="https://www.youtube.com/embed/%s" '
                'frameborder="0" '
                'allow="autoplay; encrypted-media" allowfullscreen>'
                '</iframe>' % v.vid)

            video.save()

    def corrigir_erro_causado_em_full_metadata(self):

        videos = Video.objects.all()

        for v in videos:

            for vp in v.videoparte_set.all():

                if isinstance(vp.content_object, Documento):
                    d = vp.content_object

                    if d.classe_id == 233:
                        continue

                    for r in d.revisoes.all():
                        if not r.user:
                            continue

                        if r.user.id == 76:
                            d.descricao = r.obj[0]['fields']['descricao']
                            d.save()
                            print(r.id, r.user.id, r.user, d.id, d)
                            break
