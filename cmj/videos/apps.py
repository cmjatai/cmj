import random

from django import apps
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.videos'
    label = 'videos'
    verbose_name = _('Sistema Informatizado '
                     'de Gestão Arquivística de Documentos')

    def ready(self):
        from . import signals

        from . import tasks
        from cmj.celery import app as celery_app

        return

        if settings.DEBUG or settings.FRONTEND_VERSION != 'v1' or 'www2' in __file__:
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
