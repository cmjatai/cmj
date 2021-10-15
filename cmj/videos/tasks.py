
from datetime import datetime, timedelta

from celery.utils.log import get_task_logger
from django.utils import timezone

from cmj.celery import app
from cmj.videos.functions import pull_full_metadata_video
from cmj.videos.models import Video


logger = get_task_logger(__name__)


@app.task(queue='celery', bind=True)
def task_pull_youtube(upcoming_or_live, *args, **kwargs):

    logger.debug('logger executou task_pull_youtube')
    print('print executou task_pull_youtube')

    upcoming_or_live = Video.objects.filter(
        json__snippet__liveBroadcastContent__in=('upcoming', 'live'))

    if upcoming_or_live.exists():
        for v in upcoming_or_live:
            print(v.id, v.vid, v.created, v.modified)
            try:
                v = pull_full_metadata_video(v)
            except:
                pass

        delay = timezone.now() + timedelta(seconds=10)
        task_pull_youtube.apply_async((), eta=delay)
