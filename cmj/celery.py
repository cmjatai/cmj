import os

from celery import Celery
from celery.app import shared_task

from cmj import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cmj.settings')
app = Celery('cmj')
app.config_from_object('cmj:settings', namespace='CELERY')


app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


class DebugTask(app.Task):
    name = 'DebugTaskName'

    def run(self, *args, **kwargs):
        print('print DebugTaskName')
        print('args', args)
        print('kwargs', kwargs)
        return True


@shared_task()
def debug_task(instance):
    d = DebugTask()
    d.run()
