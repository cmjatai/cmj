import os
from celery import Celery
from cmj import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cmj.settings')
app = Celery('cmj')
app.config_from_object('cmj:settings', namespace='CELERY')


app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


# @app.task(bind=True)
# def debug_task(self, teste):
#     print('teste: ', teste)
#     print('Request: {0!r}'.format(self.request))
