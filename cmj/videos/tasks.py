
from datetime import timedelta
import logging

from django.utils import timezone
import dateutil.parser

from cmj.celery import app
from cmj.videos.functions import pull_youtube_metadata_video, pull_youtube,\
    vincular_sistema_aos_videos, video_documento_na_galeria
from cmj.videos.models import Video


logger = logging.getLogger(__name__)


@app.task(queue='celery', bind=True)
def task_pull_youtube_geral(*args, **kwargs):

    logger.debug('----------- logger task_pull_youtube_geral')

    v = Video.objects.all(
    ).order_by('execucao', '-created').first()

    if v:
        try:
            v = pull_youtube_metadata_video(v)
            logger.info(
                f'pull geral  {v.id} {v.vid} {v.created} {v.modified}')

        except:
            pass

        delay = timezone.now() + timedelta(seconds=60)
        task_pull_youtube_geral.apply_async(eta=delay)


@app.task(queue='celery', bind=True)
def task_pull_youtube_live(*args, **kwargs):

    logger.debug('----------- logger task_pull_youtube_live')

    live = Video.objects.filter(
        json__snippet__liveBroadcastContent='live')

    if live.exists():
        for v in live:
            print(v.id, v.vid, v.created, v.modified)
            try:
                v = pull_youtube_metadata_video(v)
                logger.info(
                    f'pull live  {v.id} {v.vid} {v.created} {v.modified}')

            except:
                pass

        delay = timezone.now() + timedelta(seconds=60)
        task_pull_youtube_live.apply_async(eta=delay)


@app.task(queue='celery', bind=True)
def task_pull_youtube_upcoming(*args, **kwargs):

    logger.debug('----------- logger task_pull_youtube_upcoming')

    upcoming = Video.objects.filter(
        json__snippet__liveBroadcastContent='upcoming')

    if upcoming.exists():

        liveBroadcastContent = ''
        for v in upcoming:
            try:
                v = pull_youtube_metadata_video(v)
                logger.info(
                    f'pull comming {v.id} {v.vid} {v.created} {v.modified}')
                liveBroadcastContent = v.json['snippet']['liveBroadcastContent']
            except:
                pass

        if liveBroadcastContent == 'live':
            delay = timezone.now() + timedelta(seconds=10)
            task_pull_youtube_live.apply_async(eta=delay)
        else:
            scheduledStartTime = dateutil.parser.parse(
                v.json['liveStreamingDetails']['scheduledStartTime'])

            if scheduledStartTime < timezone.now():
                scheduledStartTime = timezone.now() + timedelta(seconds=60)

            task_pull_youtube_upcoming.apply_async(eta=scheduledStartTime)


@app.task(queue='celery', bind=True)
def task_pull_youtube(self, *args, **kwargs):

    from cmj.celery import app as celery_app

    i = celery_app.control.inspect()

    tasks = set()
    try:
        if i:
            queues = i.scheduled()
            if queues:
                for k, tarefas_agendadas in queues.items():
                    for ta in tarefas_agendadas:
                        tasks.add(ta['request']['name'])
    except:
        pass

    # pull_youtube()

    # vincular_sistema_aos_videos()
    # video_documento_na_galeria()

    now = timezone.now()

    if 'task_pull_youtube_upcoming' not in tasks:
        task_pull_youtube_upcoming.apply_async(eta=now + timedelta(seconds=10))

    if 'task_pull_youtube_live' not in tasks:
        task_pull_youtube_live.apply_async(eta=now + timedelta(seconds=20))

    if 'task_pull_youtube' not in tasks:
        if now.hour <= 1:
            task_pull_youtube.apply_async(eta=now + timedelta(hours=7))
        else:
            task_pull_youtube.apply_async(eta=now + timedelta(minutes=20))
