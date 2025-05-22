
from _hashlib import new
from asyncio.tasks import sleep
from datetime import timedelta
import logging

import dateutil.parser
from django.utils import timezone

from cmj.celery import app
from cmj.utils import start_task
from cmj.videos.functions import pull_youtube_metadata_video, pull_youtube,\
    vincular_sistema_aos_videos, video_documento_na_galeria
from cmj.videos.models import Video, PullExec


logger = logging.getLogger(__name__)



@app.task(queue='cq_videos', bind=True)
def task_pull_youtube_geral(*args, **kwargs):

    v = Video.objects.exclude(
        json__snippet__liveBroadcastContent__in=('live', 'upcoming')
    ).order_by('execucao', '-created').first()

    if v:
        print(f'TASK GERAL {v.id} {v.vid} {v.created} {v.modified}')
        try:
            v = pull_youtube_metadata_video(v)
            logger.info(
                f'TASK GERAL {v.id} {v.vid} {v.created} {v.modified}')
        except:
            pass

        start_task('cmj.videos.tasks.task_pull_youtube_geral',
                   task_pull_youtube_geral,
                   timezone.now() + timedelta(seconds=120))


@app.task(queue='cq_videos', bind=True)
def task_pull_youtube_live(*args, **kwargs):

    live = Video.objects.filter(
        json__snippet__liveBroadcastContent='live')

    if live.exists():
        for v in live:
            print(f'TASK LIVE {v.id} {v.vid} {v.created} {v.modified}')
            try:
                v = pull_youtube_metadata_video(v)
                logger.info(f'TASK LIVE {v.id} {v.vid} {v.created} {v.modified}')
            except:
                pass

        start_task('cmj.videos.tasks.task_pull_youtube_live',
                   task_pull_youtube_live,
                   timezone.now() + timedelta(seconds=300))


@app.task(queue='cq_videos', bind=True)
def task_pull_youtube_upcoming(*args, **kwargs):

    upcoming = Video.objects.filter(
        json__snippet__liveBroadcastContent='upcoming')

    if upcoming.exists():

        liveBroadcastContent = ''
        scheduledStartTime = None
        for v in upcoming:
            print(f'TASK UPCOMING {v.id} {v.vid} {v.created} {v.modified}')
            try:
                v = pull_youtube_metadata_video(v)
                logger.info(
                    f'TASK UPCOMING {v.id} {v.vid} {v.created} {v.modified}')
                liveBroadcastContent = v.json['snippet']['liveBroadcastContent']
            except Exception as e:
                print(
                    f'TASK UPCOMING ERROR {v.id} {v.vid} {v.created} {v.modified}')
                logger.error(
                    f'TASK UPCOMING {v.id} {v.vid} {v.created} {v.modified}')

            if liveBroadcastContent == 'live':
                start_task('cmj.videos.tasks.task_pull_youtube_live',
                           task_pull_youtube_live,
                           timezone.now() + timedelta(seconds=60))

            elif liveBroadcastContent == 'upcoming':

                newScheduledStartTime = dateutil.parser.parse(
                    v.json['liveStreamingDetails']['scheduledStartTime'])

                if not scheduledStartTime or newScheduledStartTime < scheduledStartTime:
                    scheduledStartTime = newScheduledStartTime

                if scheduledStartTime < timezone.now():
                    scheduledStartTime = timezone.now() + timedelta(seconds=60)

        if scheduledStartTime and scheduledStartTime < (timezone.now() + timedelta(seconds=3600)):
            start_task('cmj.videos.tasks.task_pull_youtube_upcoming',
                       task_pull_youtube_upcoming,
                       scheduledStartTime)


@app.task(queue='cq_videos', bind=True)
def task_pull_youtube(self, *args, **kwargs):

    now = timezone.now()

    td = PullExec.objects.timedelta_quota_pull()

    print(f'RUNNING Task_pull_youtube - proximo em: {td.total_seconds()}')
    logger.info(f'RUNNING Task_pull_youtube - proximo em: {td.total_seconds()}')
    new_started = start_task('cmj.videos.tasks.task_pull_youtube',
                             task_pull_youtube,
                             now + td)

    if not new_started:
        print(f'NEW_STARTED FALSE Task_pull_youtube - proximo em: {td.total_seconds()}')
        logger.info(f'NEW_STARTED FALSE Task_pull_youtube - proximo em: {td.total_seconds()}')
        return

    try:
        pull_youtube()
        vincular_sistema_aos_videos()
        video_documento_na_galeria()
    except Exception as e:
        print('ERROR in Task_pull_youtube')
        logger.error('ERROR in Task_pull_youtube')

    now = timezone.now()

    start_task('cmj.videos.tasks.task_pull_youtube_geral',
               task_pull_youtube_geral,
               now + timedelta(seconds=60))

    start_task('cmj.videos.tasks.task_pull_youtube_upcoming',
               task_pull_youtube_upcoming,
               now + timedelta(seconds=40))

    start_task('cmj.videos.tasks.task_pull_youtube_live',
               task_pull_youtube_live,
               now + timedelta(seconds=20)) 
