import logging
import random
from django import apps
from django.utils.translation import gettext_lazy as _
import inspect

from django.conf import settings

from cmj.utils import start_task
from django.utils import timezone

logger = logging.getLogger(__name__)

class AppConfig(apps.AppConfig):
    name = 'sapl.base'
    label = 'base'
    verbose_name = _('Dados Básicos')

    def ready(self):
        from . import signals
        from . import tasks

        from cmj.celery import app as celery_app
        from sapl.base.tasks import task_analise_similaridade_entre_materias

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

        #time_sleep = 60 + random.randint(0, 300)

        #logger.info(f'Iniciando task_analise_similaridade_entre_materias em {time_sleep} segundos')
        #start_task(
        #    'sapl.base.tasks.task_analise_similaridade_entre_materias',
        #    task_analise_similaridade_entre_materias,
        #    timezone.now() + timezone.timedelta(seconds=120)
        #)
