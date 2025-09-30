
# timer_app/tasks.py - Tarefas assíncronas com Celery
from celery import shared_task
from .timer_manager import TimerManager
from .models import Timer, TimerState
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_finished_timers():
    """
    Tarefa periódica para verificar cronômetros que terminaram
    Deve ser executada a cada segundo via Celery Beat
    """
    timer_manager = TimerManager()
    finished_timers = timer_manager.check_finished_timers()

    if finished_timers:
        logger.info(f"Finalizados {len(finished_timers)} cronômetros")
        for timer in finished_timers:
            logger.info(f"Timer {timer.name} (ID: {timer.id}) finalizado")

    return len(finished_timers)

@shared_task
def cleanup_old_events():
    """
    Tarefa para limpar eventos antigos (opcional)
    Manter apenas eventos dos últimos 30 dias
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import TimerEvent

    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = TimerEvent.objects.filter(timestamp__lt=cutoff_date).delete()[0]

    logger.info(f"Removidos {deleted_count} eventos antigos")
    return deleted_count

@shared_task
def generate_timer_report(timer_id):
    """Gerar relatório de uso de um cronômetro"""
    try:
        timer = Timer.objects.get(id=timer_id)
        events = timer.events.all().order_by('timestamp')

        report_data = {
            'timer_name': timer.name,
            'total_events': events.count(),
            'start_events': events.filter(event_type='started').count(),
            'pause_events': events.filter(event_type='paused').count(),
            'stop_events': events.filter(event_type='stopped').count(),
            'finish_events': events.filter(event_type='finished').count(),
        }

        return report_data
    except Timer.DoesNotExist:
        return {'error': 'Timer not found'}
