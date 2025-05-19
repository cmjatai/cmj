import os

from celery import Celery
from celery.app import shared_task

from cmj import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cmj.settings')

app = Celery('cmj')
app.conf.enable_utc = False
app.config_from_object('cmj:settings', namespace='CELERY')


app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


