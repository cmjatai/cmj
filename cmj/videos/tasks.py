
from asyncio.tasks import sleep
from datetime import timedelta
import logging

from django.utils import timezone
import dateutil.parser

from cmj.celery import app
from cmj.videos.functions import pull_youtube_metadata_video, pull_youtube,\
    vincular_sistema_aos_videos, video_documento_na_galeria
from cmj.videos.models import Video, PullExec


logger = logging.getLogger(__name__)


def get_tasks_scheduled():

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
    return tasks


def start_task(task_name, task, eta):

    tasks = get_tasks_scheduled()
    #t_str = ', '.join(tasks)

    #logger.debug(f'{task_name} {eta} SET: {t_str}')

    if f'cmj.videos.tasks.{task_name}' not in tasks:
        logger.debug(f'START TRUE {task_name} {eta}')
        task.apply_async(eta=eta)
        return True
    logger.debug(f'START FALSE {task_name} {eta}')
    return False


@app.task(queue='celery', bind=True)
def task_pull_youtube_geral(*args, **kwargs):

    v = Video.objects.all(
    ).order_by('execucao', '-created').first()

    if v:
        try:
            v = pull_youtube_metadata_video(v)
            logger.info(
                f'TASK GERAL {v.id} {v.vid} {v.created} {v.modified}')

        except:
            pass

        start_task('task_pull_youtube_geral',
                   task_pull_youtube_geral,
                   timezone.now() + timedelta(seconds=60))


@app.task(queue='celery', bind=True)
def task_pull_youtube_live(*args, **kwargs):

    live = Video.objects.filter(
        json__snippet__liveBroadcastContent='live')

    if live.exists():
        for v in live:
            print(v.id, v.vid, v.created, v.modified)
            try:
                v = pull_youtube_metadata_video(v)
                logger.info(
                    f'TASK LIVE {v.id} {v.vid} {v.created} {v.modified}')

            except:
                pass

        start_task('task_pull_youtube_live',
                   task_pull_youtube_live,
                   timezone.now() + timedelta(seconds=60))


@app.task(queue='celery', bind=True)
def task_pull_youtube_upcoming(*args, **kwargs):

    upcoming = Video.objects.filter(
        json__snippet__liveBroadcastContent='upcoming')

    if upcoming.exists():

        liveBroadcastContent = ''
        for v in upcoming:
            try:
                v = pull_youtube_metadata_video(v)
                logger.info(
                    f'TASK UPCOMING {v.id} {v.vid} {v.created} {v.modified}')
                liveBroadcastContent = v.json['snippet']['liveBroadcastContent']
            except:
                pass

        if liveBroadcastContent == 'live':
            start_task('task_pull_youtube_live',
                       task_pull_youtube_live,
                       timezone.now() + timedelta(seconds=60))

        elif liveBroadcastContent == 'upcoming':
            scheduledStartTime = dateutil.parser.parse(
                v.json['liveStreamingDetails']['scheduledStartTime'])

            if scheduledStartTime < timezone.now():
                scheduledStartTime = timezone.now() + timedelta(seconds=60)

            start_task('task_pull_youtube_upcoming',
                       task_pull_youtube_upcoming,
                       scheduledStartTime)


@app.task(queue='celery', bind=True)
def task_pull_youtube(self, *args, **kwargs):

    now = timezone.now()

    td = PullExec.objects.timedelta_quota_pull()

    logger.debug(
        f'RUNNING Task_pull_youtube - proximo em: {td.total_seconds()}')
    new_started = start_task('task_pull_youtube',
                             task_pull_youtube,
                             now + td)

    if not new_started:
        return
    pull_youtube()
    vincular_sistema_aos_videos()
    video_documento_na_galeria()

    now = timezone.now()

    start_task('task_pull_youtube_geral',
               task_pull_youtube_geral,
               now + timedelta(seconds=60))

    start_task('task_pull_youtube_upcoming',
               task_pull_youtube_upcoming,
               now + timedelta(seconds=40))

    start_task('task_pull_youtube_live',
               task_pull_youtube_live,
               now + timedelta(seconds=20))