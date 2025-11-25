# cronometro_app/tasks.py - Tarefas assíncronas com Celery
from datetime import timedelta
from celery import shared_task

from cmj.painelset.tasks_function import task_refresh_states_from_visaodepainel_function
from cmj.utils import TimeExecution
from .cronometro_manager import CronometroManager
from .models import Cronometro, CronometroState
import logging
from django.conf import settings
from django.utils import timezone
from pythonosc import udp_client
from cmj.celery import app as cmj_celery_app

from celery.utils.log import get_task_logger

logger = logging.getLogger(__name__)

logger_celery = get_task_logger(__name__)

porta = 10023
clients = {}

SEND_MESSAGE_MICROPHONE = True


@cmj_celery_app.task(queue='cq_painelset', bind=True)
def task_cancel_auto_corte_microfone(self, individuo_id):
    """Cancelar o auto corte de microfone após religar manualmente"""
    from .models import Individuo
    try:
        individuo = Individuo.objects.get(id=individuo_id)
        if individuo.auto_corte_microfone:
            individuo.auto_corte_microfone = False
            individuo.save()
            logger_celery.info(f"Auto corte de microfone cancelado para {individuo}")
    except Individuo.DoesNotExist:
        logger_celery.error(f"Individuo com ID {individuo_id} não encontrado para cancelar auto corte de microfone")


def task_check_finished_cronometros_function():
    global client
    cronometro_manager = CronometroManager()
    zero_time_cronometros, running_cronometros = cronometro_manager.check_zero_timer()

    if SEND_MESSAGE_MICROPHONE or not settings.DEBUG:
        remove_ips = []
        for ip, client_info in clients.items():
            client = client_info['client']
            if 'last_send' in client_info and (timezone.now() - client_info['last_send']) > timedelta(seconds=300):
                logger_celery.info(f"Removendo cliente OSC {client._address}:{client._port} por inatividade")
                remove_ips.append(ip)
            elif 'last_ping' in client_info and (timezone.now() - client_info['last_ping']) > timedelta(seconds=7):
                try:
                    logger_celery.debug(f"Enviando comando /xremote para {client._address}:{client._port} por inatividade")
                    client.send_message("/xremote", None)
                    client_info['last_ping'] = timezone.now()
                except Exception as e:
                    logger_celery.error(f"Erro ao enviar mensagem OSC para {client._address}:{client._port}: {e}")
                    remove_ips.append(ip)

        for ip in remove_ips:
            try:
                clients[ip]['client'].close()
            except:
                pass
            del clients[ip]

    if zero_time_cronometros:

        logger_celery.info(f"Finalizados {len(zero_time_cronometros)} cronômetros")

        for cronometro in zero_time_cronometros:
            individuo = cronometro.vinculo
            evento = individuo.evento if individuo else None
            corte_religar = individuo.tempo_de_corte_microfone.total_seconds() if individuo else 10
            corte_religar = min(0, -1 * corte_religar)  # Tornar negativo

            if not evento.comunicar_com_mesas:
                continue

            if not individuo or individuo.microfone_sempre_ativo:
                continue

            ips = individuo.ips

            for ip in ips:
                if ip not in clients and (SEND_MESSAGE_MICROPHONE or not settings.DEBUG):
                    clients[ip] = {
                        'client': udp_client.SimpleUDPClient(ip, porta),
                        'last_ping': timezone.now(),
                        'last_send': timezone.now()
                    }

            remaining_time = cronometro.remaining_time

            logger_celery.info(f"Cronometro {cronometro.name} (ID: {cronometro.id}) tempo encerrado")

            for ip in ips:
                client_info = clients.get(ip)

                if not client_info:
                    continue

                client = client_info['client']

                try:
                    if timedelta(seconds=int(corte_religar*(1.5))) < remaining_time < timedelta(seconds=corte_religar):
                        logger_celery.debug(f"Microfone religado para o cronômetro {cronometro.name} (ID: {cronometro.id})")
                        individuo.status_microfone = True
                        individuo.auto_corte_microfone = False
                        individuo.save()
                        if individuo.status_microfone:
                            if client and (SEND_MESSAGE_MICROPHONE or not settings.DEBUG):
                                #client.send_message(f"/ch/{individuo.channel_display}/mix/on", 1 )
                                client.send_message(f"/ch/{individuo.channel_display}/mix/on", 1 )
                                client_info['last_send'] = timezone.now()
                                client_info['last_ping'] = timezone.now()

                    elif timedelta(seconds=corte_religar) < remaining_time < timedelta(seconds=2):
                        logger_celery.debug(f"Corte de microfone detectado no cronômetro {cronometro.name} (ID: {cronometro.id})")
                        if individuo.status_microfone and not individuo.auto_corte_microfone:
                            individuo.status_microfone = False
                            individuo.auto_corte_microfone = True
                            individuo.save()

                            task_cancel_auto_corte_microfone.apply_async(
                                args=[individuo.id],
                                countdown=-1 * corte_religar)

                        if not individuo.status_microfone and individuo.auto_corte_microfone:
                            if client and (SEND_MESSAGE_MICROPHONE or not settings.DEBUG):
                                client_info['last_ping'] = timezone.now()
                                client.send_message(f"/ch/{individuo.channel_display}/mix/on", 0)


                except Exception as e:
                    logger_celery.error(f"Erro ao enviar mensagem OSC para {ip}: {e}")
                    del clients[ip]

    return zero_time_cronometros, running_cronometros

@shared_task
def task_painelset_refresh_states():

    zero_time_cronometros, running_cronometros = task_check_finished_cronometros_function()

    task_refresh_states_from_visaodepainel_function()