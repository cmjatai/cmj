from django import apps
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

        i = celery_app.control.inspect()

        try:
            if i:
                queues = i.scheduled()
                if queues:
                    for k, tarefas_agendadas in queues.items():
                        for ta in tarefas_agendadas:
                            if ta['request']['name'] == 'cmj.videos.tasks.task_pull_youtube':
                                return
        except:
            pass
        tasks.task_pull_youtube.apply_async(countdown=10)
