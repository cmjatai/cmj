import json

from django.conf import settings
from django.utils import timezone

from cmj.sigad.models import Documento
import requests as rq


def pull_full_metadata_video(v):

    # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'}
    headers = {}
    headers["Referer"] = settings.SITE_URL
    headers['Content-Type'] = 'application/json'

    url_search = ('https://www.googleapis.com/youtube/v3/videos'
                  '?key={}'
                  '&id={}'
                  '&part=snippet,id,contentDetails,statistics,liveStreamingDetails')

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
                    d.save()
                elif dp.tipo == Documento.TPD_VIDEO:
                    dp.extra_data = v.json
                    dp.save()
    return v
