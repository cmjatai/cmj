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

# Configuração de tarefas periódicas
#from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-finished-cronometros': {
        'task': 'cmj.painelset.tasks.check_finished_cronometros',
        'schedule': 1.0,  # A cada segundo
    },
    #'cleanup-old-events': {
    #    'task': 'cmj.painelset.tasks.cleanup_old_events',
    #    'schedule': crontab(hour=2, minute=0),  # Diariamente às 2h
    #},
}
