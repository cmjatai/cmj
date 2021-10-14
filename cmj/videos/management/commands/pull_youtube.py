
from datetime import timedelta
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

        m.desativa_auto_now()

        # self.corrigir_erro_causado_em_full_metadata()
        # return

        if not settings.DEBUG:
            self.pull_youtube()
        self.get_full_metadata_video()

        m.ativa_auto_now()

        self.vincular_sistema_aos_videos()

        self.video_documento_na_galeria()

    def get_full_metadata_video(self):
        videos = Video.objects.all().order_by('execucao', '-created')

        videos = videos[:100]

        now = timezone.now()

        for v in videos:
            print(v.id, v.vid, v)
            r = ''
            try:

                # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
                headers = {}
                headers["Referer"] = settings.SITE_URL
                headers['Content-Type'] = 'application/json'

                url_search = ('https://www.googleapis.com/youtube/v3/videos'
                              '?key={}'
                              '&id={}'
                              '&part=snippet,id,contentDetails,statistics')

                #'&channelId=UCZXKjzKW2n1w4JQ3bYlrA-w'

                url = url_search.format(
                    settings.GOOGLE_URL_API_NEW_KEY,
                    v.vid
                )

                r = rq.get(url, headers=headers)

                data = r._content.decode('utf-8')

                r = json.loads(data)

                v.json = r['items'][0]

                try:
                    peso = timezone.now().year - v.created.year
                    peso = peso if peso else 1
                except:
                    peso = 1
                v.execucao += peso
                v.save()
                for vp in v.videoparte_set.all():

                    if isinstance(vp.content_object, Documento):
                        d = vp.content_object

                        if d.classe_id != 233:
                            continue

                        for dp in d.treechilds2list():
                            if dp == d:
                                d.extra_data = v.json
                                d.descricao = v.json['snippet']['description']
                                d.save()
                            elif dp.tipo == Documento.TPD_VIDEO:
                                dp.extra_data = v.json
                                dp.save()
            except:
                pass

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

    def pull_youtube(self):

        py = PullYoutube.objects.last()

        if not py:
            data_base = dateutil.parser.parse('2013-11-01T00:00:00Z')
            data_base = timezone.localtime(data_base)
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

        # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
        headers = {}
        headers["Referer"] = settings.SITE_URL
        headers['Content-Type'] = 'application/json'

        url_search = ('https://www.googleapis.com/youtube/v3/search'
                      '?key={}'
                      '&pageToken={}'
                      '&publishedAfter={}'
                      '&publishedBefore={}'
                      '&channelId=UCZXKjzKW2n1w4JQ3bYlrA-w'
                      '&part=snippet,id&order=date&maxResults=50')

        now = timezone.localtime()

        pulls = list(PullYoutube.objects.all().order_by('execucao', '-id')[:3])
        if 9 <= now.hour <= 17 and 0 <= now.weekday() <= 4:
            pull_atual = PullYoutube.objects.all().order_by('-id').first()
            if pull_atual not in pulls:
                pulls.insert(0, pull_atual)

        for pull in pulls:

            pageToken = ''

            publishedBefore = pull.published_before.isoformat('T')[:19] + 'Z'
            publishedAfter = pull.published_after.isoformat('T')[:19] + 'Z'

            while pageToken is not None:

                url = url_search.format(
                    settings.GOOGLE_URL_API_NEW_KEY,
                    pageToken,
                    publishedAfter,
                    publishedBefore
                )

                r = rq.get(url, headers=headers)

                data = r._content.decode('utf-8')

                r = json.loads(data)

                pageToken = None

                if 'nextPageToken' in r:
                    pageToken = r['nextPageToken']

                if not 'items' in r:
                    continue

                for i in r['items']:

                    if not 'videoId' in i['id']:
                        continue

                    qs = Video.objects.filter(vid=i['id']['videoId'])

                    if qs.exists():
                        continue

                    v = Video()
                    v.json = i
                    v.vid = i['id']['videoId']
                    v.titulo = i['snippet']['title']
                    v.owner_id = 1
                    v.modifier_id = 1

                    v.created = dateutil.parser.parse(
                        i['snippet']['publishedAt'])
                    v.modified = dateutil.parser.parse(
                        i['snippet']['publishedAt'])

                    v.save()

                # if stop_page:
                #    pageToken = None
            pull.execucao += 1
            pull.save()

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
