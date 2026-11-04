import logging
from datetime import timedelta

import dateutil.parser
from celery.utils.log import get_task_logger
from django.utils import timezone

from cmj.celery import app
from cmj.utils import start_task
from cmj.videos.functions import (
    pull_youtube,
    pull_youtube_metadata_video,
    video_documento_na_galeria,
    vincular_sistema_aos_videos,
)
from cmj.videos.models import PullExec, Video

logger = logging.getLogger(__name__)
logger_celery = get_task_logger(__name__)


@app.task(queue="cq_videos", bind=True)
def task_pull_youtube_geral(*args, **kwargs):

    v = (
        Video.objects.exclude(
            json__snippet__liveBroadcastContent__in=("live", "upcoming")
        )
        .order_by("execucao", "-created")
        .first()
    )

    if v:
        logger_celery.info(f"TASK GERAL {v.id} {v.vid} {v.created} {v.modified}")
        try:
            v, executado = pull_youtube_metadata_video(v)
            if not executado:
                return
            logger_celery.info(f"TASK GERAL {v.id} {v.vid} {v.created} {v.modified}")
        except:
            pass

        start_task(
            "cmj.videos.tasks.task_pull_youtube_geral",
            task_pull_youtube_geral,
            timezone.now() + timedelta(seconds=120),
            _logger=logger_celery,
        )


@app.task(queue="cq_videos", bind=True)
def task_pull_youtube_live(*args, **kwargs):

    live = Video.objects.filter(json__snippet__liveBroadcastContent="live")

    if live.exists():
        for v in live:
            logger_celery.info(f"TASK LIVE {v.id} {v.vid} {v.created} {v.modified}")
            try:
                v, executado = pull_youtube_metadata_video(v)
                if not executado:
                    continue
                logger_celery.info(f"TASK LIVE {v.id} {v.vid} {v.created} {v.modified}")
            except:
                pass

        start_task(
            "cmj.videos.tasks.task_pull_youtube_live",
            task_pull_youtube_live,
            timezone.now() + timedelta(seconds=300),
            _logger=logger_celery,
        )


@app.task(queue="cq_videos", bind=True)
def task_pull_youtube_upcoming(*args, **kwargs):

    upcoming = Video.objects.filter(json__snippet__liveBroadcastContent="upcoming")

    if upcoming.exists():

        liveBroadcastContent = ""
        scheduledStartTime = None
        for v in upcoming:
            logger_celery.info(f"TASK UPCOMING {v.id} {v.vid} {v.created} {v.modified}")
            try:
                v, executado = pull_youtube_metadata_video(v)
                if not executado:
                    continue
                logger_celery.info(
                    f"TASK UPCOMING {v.id} {v.vid} {v.created} {v.modified}"
                )
                liveBroadcastContent = v.json["snippet"]["liveBroadcastContent"]
            except Exception as e:
                logger_celery.error(
                    f"TASK UPCOMING ERROR DETAILS {v.id} {v.vid} {v.created} {v.modified} - {str(e)}"
                )
                continue

            if liveBroadcastContent == "live":
                start_task(
                    "cmj.videos.tasks.task_pull_youtube_live",
                    task_pull_youtube_live,
                    timezone.now() + timedelta(seconds=60),
                    _logger=logger_celery,
                )

            elif liveBroadcastContent == "upcoming":

                newScheduledStartTime = dateutil.parser.parse(
                    v.json["liveStreamingDetails"]["scheduledStartTime"]
                )

                if not scheduledStartTime or newScheduledStartTime < scheduledStartTime:
                    scheduledStartTime = newScheduledStartTime

                if scheduledStartTime < timezone.now():
                    scheduledStartTime = timezone.now() + timedelta(seconds=60)

        if scheduledStartTime and scheduledStartTime < (
            timezone.now() + timedelta(seconds=3600)
        ):
            start_task(
                "cmj.videos.tasks.task_pull_youtube_upcoming",
                task_pull_youtube_upcoming,
                scheduledStartTime,
                _logger=logger_celery,
            )


@app.task(queue="cq_videos", bind=True)
def task_pull_youtube(self, *args, **kwargs):

    now = timezone.now()

    td = PullExec.objects.timedelta_quota_pull()

    logger_celery.info(f"RUNNING Task_pull_youtube - proximo em: {td.total_seconds()}")
    new_started = start_task(
        "cmj.videos.tasks.task_pull_youtube",
        task_pull_youtube,
        now + td,
        _logger=logger_celery,
    )

    if not new_started:
        logger_celery.info(f"NEW_STARTED FALSE Task_pull_youtube - proximo em: {td.total_seconds()}")
        return

    try:
        pull_youtube()
        vincular_sistema_aos_videos()
        video_documento_na_galeria()
    except Exception as e:
        logger_celery.error("ERROR in Task_pull_youtube")
        logger_celery.error(str(e))

    now = timezone.now()

    start_task(
        "cmj.videos.tasks.task_pull_youtube_geral",
        task_pull_youtube_geral,
        now + timedelta(seconds=60),
        _logger=logger_celery,
    )

    start_task(
        "cmj.videos.tasks.task_pull_youtube_upcoming",
        task_pull_youtube_upcoming,
        now + timedelta(seconds=40),
        _logger=logger_celery,
    )

    start_task(
        "cmj.videos.tasks.task_pull_youtube_live",
        task_pull_youtube_live,
        now + timedelta(seconds=20),
        _logger=logger_celery,
    )
