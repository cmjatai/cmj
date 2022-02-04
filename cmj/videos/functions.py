
from datetime import timedelta
import json
import logging
from random import random
import re

import dateutil.parser
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from cmj.sigad.models import Documento
from cmj.videos.models import PullYoutube, Video, VideoParte, PullExec
import requests as rq


logger = logging.getLogger(__name__)

DEBUG_TASKS = settings.DEBUG


def pull_youtube_metadata_video(v):

    # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    headers = {}
    headers["Referer"] = settings.SITE_URL
    headers['Content-Type'] = 'application/json'

    url_search = ('https://www.googleapis.com/youtube/v3/videos'
                  '?key={}'
                  '&id={}'
                  '&part=snippet,id,contentDetails,statistics,liveStreamingDetails')

    #'&channelId=UCZXKjzKW2n1w4JQ3bYlrA-w'

    if not DEBUG_TASKS:
        url = url_search.format(
            settings.GOOGLE_URL_API_NEW_KEY,
            v.vid
        )

        r = rq.get(url, headers=headers)

        data = r._content.decode('utf-8')

        r = json.loads(data)

        v.json = r['items'][0]

    now = timezone.now()

    p = PullExec()
    p.pull = PullYoutube.objects.pull_from_date()
    p.quota = 1
    p.save()

    try:
        peso = now.year - v.created.year
        peso = peso if peso else 1
    except:
        peso = 1

    v.execucao += peso
    v.titulo = v.json['snippet']['title']
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
                    d.public_date = dateutil.parser.parse(
                        v.json['snippet']['publishedAt'])
                    d.save()
                elif dp.tipo == Documento.TPD_VIDEO:
                    dp.extra_data = v.json
                    dp.save()

    return v


def update_auto_now(m, disabled=True):

    for f in m._meta.get_fields():
        dua = f

        if disabled:
            if hasattr(dua, 'auto_now'):
                dua._auto_now = dua.auto_now
                dua.auto_now = False

            if hasattr(dua, 'auto_now_add'):
                dua._auto_now_add = dua.auto_now_add
                dua.auto_now_add = False
        else:
            if hasattr(dua, '_auto_now'):
                dua.auto_now = dua._auto_now

            if hasattr(dua, '_auto_now_add'):
                dua.auto_now_add = dua._auto_now_add


def pull_youtube():

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

    now = timezone.now()

    pull_atual = PullYoutube.objects.pull_from_date()

    pulls = PullYoutube.objects.exclude(
        id=pull_atual.id).order_by('execucao', '-id').first()

    if pull_atual not in pulls:
        pulls.insert(0, pull_atual)

    update_auto_now(Video, disabled=True)

    for pull in pulls:

        pageToken = ''

        publishedBefore = pull.published_before.isoformat('T')[:19] + 'Z'
        publishedAfter = pull.published_after.isoformat('T')[:19] + 'Z'

        logger.info(f'pull new video {publishedBefore} {publishedAfter}')

        while pageToken is not None:

            p = PullExec()
            p.pull = pull
            p.quota = 100
            p.save()

            r = None

            if not DEBUG_TASKS:
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

            if not r:
                continue

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

        try:
            peso = now.year - pull.publishedBefore.year
            peso = peso if peso else 1
        except:
            peso = 1

        pull.execucao += peso
        pull.save()
    update_auto_now(Video, disabled=False)


def vincular_sistema_aos_videos():

    if DEBUG_TASKS:
        return

    videos = Video.objects.order_by('-created')

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
                            """if hasattr(i, 'titulo') and i.titulo != v.titulo:
                                if hasattr(i, 'classe_id') and i.classe_id == 233:
                                    i.titulo = v.titulo
                                    i.descricao = v.json['snippet']['description']
                                    i.save()"""
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


def video_documento_na_galeria():

    if DEBUG_TASKS:
        return

    videos = Video.objects.order_by('-created')

    ct_doc = ContentType.objects.get_for_model(Documento)
    created = False
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
        created = True

    if created:
        vincular_sistema_aos_videos()
