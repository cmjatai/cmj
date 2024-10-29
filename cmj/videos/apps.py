import inspect
import random

from django import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from cmj.utils import get_celery_worker_status


class AppConfig(apps.AppConfig):
    name = 'cmj.videos'
    label = 'videos'
    verbose_name = _('Sistema Informatizado '
                     'de Gestão Arquivística de Documentos')

    def ready(self):
        from . import signals

        from . import tasks

        from cmj.celery import app as celery_app

        for i in inspect.stack():
            try:
                if i.frame.f_locals['subcommand'] == 'migrate':
                    return
            except Exception as e:
                pass

        #status_celery = get_celery_worker_status()

        if settings.DEBUG:
            return

        if 'sqlite3' in settings.DATABASES['default']['ENGINE']:
            return

        try:
            i = celery_app.control.inspect()

            if not i.registered():
                return

            if i:
                queues = i.scheduled()
                if queues:
                    for k, tarefas_agendadas in queues.items():
                        for ta in tarefas_agendadas:
                            if ta['request']['name'] == 'cmj.videos.tasks.task_pull_youtube':
                                return
            tasks.task_pull_youtube.apply_async(
                countdown=int(60 + random.random() * 120)
            )
        except:
            pass


"""
from cmj.celery import app as celery_app
i = celery_app.control.inspect()
if i:
    queues = i.scheduled()
    if queues:
        for k, tarefas_agendadas in queues.items():
            for ta in tarefas_agendadas:
                print(ta['eta'], ta['request']['name'])
print('-----------------------------')
print(timezone.now())


     from celery import current_app as cap
    ...: from time import sleep
    ...: i = cap.control.inspect()
    ...: while True:
    ...:     q = i.scheduled()
    ...:     for k, v in q.items():
    ...:         print(k, v)
    ...:     break

"""
