from pydoc import cli
from cmj.celery import app as cmj_celery_app

# cronometro_app/tasks.py - Tarefas assíncronas com Celery
from datetime import timedelta
from celery import shared_task
from .cronometro_manager import CronometroManager
from .models import Cronometro, CronometroState
import logging
from django.conf import settings
from django.utils import timezone
from pythonosc import udp_client
#from cmj.celery import app as cmj_celery_app

#logger = logging.getLogger(__name__)
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

ip = "10.3.163.123"  # Substitua pelo endereço IP da sua mesa
porta = 10023
clients = {}
corte_religar = -5  # segundos para considerar corte de tempo

SEND_MESSAGE_MICROPHONE = False

def check_finished_cronometros_function():
    global client
    cronometro_manager = CronometroManager()
    zero_time_cronometros, running_cronometros = cronometro_manager.check_zero_timer()

    if zero_time_cronometros:

        logger.info(f"Finalizados {len(zero_time_cronometros)} cronômetros")

        for cronometro in zero_time_cronometros:
            individuo = cronometro.vinculo
            evento = individuo.evento if individuo else None

            if not evento.comunicar_com_mesas:
                continue

             # Pular se o indivíduo não existir ou se o microfone for sempre ativo

            if not individuo or individuo.microfone_sempre_ativo:
                continue

            if not individuo.ips_mesas:
                if not evento.ips_mesas:
                    continue
                else:
                    ips = [ip.strip() for ip in evento.ips_mesas.split(' ') if ip.strip()]
            else:
                ips = [ip.strip() for ip in individuo.ips_mesas.split(' ') if ip.strip()]

            for ip in ips:
                if ip not in clients and (SEND_MESSAGE_MICROPHONE or not settings.DEBUG):
                    clients[ip] = {
                        'client': udp_client.SimpleUDPClient(ip, porta),
                        'last_used': timezone.now()
                    }

            remaining_time = cronometro.remaining_time

            logger.info(f"Cronometro {cronometro.name} (ID: {cronometro.id}) tempo encerrado")

            for ip in ips:
                client_info = clients.get(ip)

                if not client_info:
                    continue

                client = client_info['client']

                try:
                    if 'last_used' in client_info and (timezone.now() - client_info['last_used']) > timedelta(seconds=7):
                        logger.info(f"Enviando comando /xremote para {ip} por inatividade")
                        client.send_message("/xremote", None)

                    if remaining_time < timedelta(seconds=corte_religar) and not individuo.status_microfone:
                        logger.info(f"Microfone religado para o cronômetro {cronometro.name} (ID: {cronometro.id})")
                        individuo.status_microfone = True
                        individuo.save()
                        if client and (SEND_MESSAGE_MICROPHONE or not settings.DEBUG):
                            client.send_message(f"/ch/{individuo.channel_display}/mix/on", 1 )
                            client_info['last_used'] = timezone.now()

                    elif timedelta(seconds=corte_religar) < remaining_time < timedelta() and individuo.status_microfone:
                        logger.info(f"Corte de microfone detectado no cronômetro {cronometro.name} (ID: {cronometro.id})")
                        individuo.status_microfone = False
                        individuo.save()
                        if client and (SEND_MESSAGE_MICROPHONE or not settings.DEBUG):
                            client.send_message(f"/ch/{individuo.channel_display}/mix/on", 0)
                            client_info['last_used'] = timezone.now()

                except Exception as e:
                    logger.error(f"Erro ao enviar mensagem OSC para {ip}: {e}")
                    del clients[ip]

    return len(zero_time_cronometros)

@shared_task
def check_finished_cronometros():
    print("check_finished_cronometros")
    logger.info("Iniciando verificação de cronômetros finalizados...")
    check_finished_cronometros_function()
    logger.info("Verificação de cronômetros finalizados concluída.")

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

def check_finished_cronometros__old():
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