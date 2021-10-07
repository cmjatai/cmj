
from _functools import reduce
from datetime import datetime, timedelta
from random import random
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q, F
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
import dateutil.parser

from cmj.signals import Manutencao
from cmj.videos.models import Video, PullYoutube
import requests as rq


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):
        m = Manutencao()
        m.desativa_auto_now()
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        # Video.objects.all().update(created=F('modified'))

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

        self.pull_youtube()

    def pull_youtube(self):

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
        if 7 < now.hour < 21:
            pull_atual = PullYoutube.objects.all().order_by('-id').first()
            if pull_atual not in pulls:
                pulls.insert(0, pull_atual)

        for pull in pulls:

            reduce

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

                stop_page = False
                if not 'items' in r:
                    continue

                for i in r['items']:

                    if not 'videoId' in i['id']:
                        continue

                    qs = Video.objects.filter(vid=i['id']['videoId'])

                    if qs.exists():
                        stop_page = True
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
