
from datetime import datetime, timedelta
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.signals import post_delete, post_save
from django.utils import timezone
import dateutil.parser

from cmj.signals import Manutencao
from cmj.videos.models import Video
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

        data_base = timezone.now()
        td = timedelta(days=10)

        while True:
            print(data_base)
            pageToken = ''

            publishedBefore = data_base.isoformat('T')[:19] + 'Z'
            data_base = data_base - td
            publishedAfter = data_base.isoformat('T')[:19] + 'Z'

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

            if data_base.year < 2013:
                return
