
# cronometro_app/tasks.py - Tarefas assíncronas com Celery
from celery import shared_task
from .cronometro_manager import CronometroManager
from .models import Cronometro, CronometroState
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_finished_cronometros():
    """
    Tarefa periódica para verificar cronômetros que terminaram
    Deve ser executada a cada segundo via Celery Beat
    """
    cronometro_manager = CronometroManager()
    finished_cronometros = cronometro_manager.check_finished_cronometros()

    if finished_cronometros:
        logger.info(f"Finalizados {len(finished_cronometros)} cronômetros")
        for cronometro in finished_cronometros:
            logger.info(f"Cronometro {cronometro.name} (ID: {cronometro.id}) finalizado")

    return len(finished_cronometros)

@shared_task
def cleanup_old_events():
    """
    Tarefa para limpar eventos antigos (opcional)
    Manter apenas eventos dos últimos 30 dias
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import CronometroEvent

    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = CronometroEvent.objects.filter(timestamp__lt=cutoff_date).delete()[0]

    logger.info(f"Removidos {deleted_count} eventos antigos")
    return deleted_count

@shared_task
def generate_cronometro_report(cronometro_id):
    """Gerar relatório de uso de um cronômetro"""
    try:
        cronometro = Cronometro.objects.get(id=cronometro_id)
        events = cronometro.events.all().order_by('timestamp')

        report_data = {
            'cronometro_name': cronometro.name,
            'total_events': events.count(),
            'start_events': events.filter(event_type='started').count(),
            'pause_events': events.filter(event_type='paused').count(),
            'stop_events': events.filter(event_type='stopped').count(),
            'finish_events': events.filter(event_type='finished').count(),
        }

        return report_data
    except Cronometro.DoesNotExist:
        return {'error': 'Cronometro not found'}
