from django import apps
from django.utils.translation import gettext_lazy as _
import inspect
import random

from django.conf import settings

class AppConfig(apps.AppConfig):
    name = 'sapl.base'
    label = 'base'
    verbose_name = _('Dados Básicos')

    def ready(self):
        from . import signals
        from . import tasks
        from cmj.celery import app as celery_app

        apps.AppConfig.ready(self)

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
                            if ta['request']['name'] == 'sapl.base.tasks.task_analise_similaridade_entre_materias':
                                return
            tasks.task_analise_similaridade_entre_materias.apply_async(
                countdown=int(60 + random.random() * 120)
            )
        except:
            pass