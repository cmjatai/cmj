from datetime import timedelta
import logging
import time
from time import sleep

from django.apps.registry import apps
from django.conf import settings
from django.utils import formats
from django.db import transaction

from cmj.api.serializers_painelset import CronometroSerializer, CronometroTreeSerializer, EventoSerializer, IndividuoSerializer
from cmj.painelset.cronometro_manager import CronometroManager
from cmj.painelset.models import Cronometro, CronometroState, Evento, Individuo, Painel, VisaoDePainel
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import BasePermission
from rest_framework import serializers
from rest_framework import status
from django.utils import timezone
from pythonosc import udp_client

from cmj.painelset.tasks import SEND_MESSAGE_MICROPHONE
from sapl.api.mixins import ResponseFileMixin
from sapl.base.templatetags.common_tags import youtube_id

logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('painelset')
    ]
)

cronometro_manager = CronometroManager()

class EventoChangePermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.has_perm('painelset.change_evento')

@customize(Evento)
class _EventoViewSet:
    serializer_class = EventoSerializer

    @action(detail=True, methods=['PATCH'], permission_classes=[EventoChangePermission])
    def start(self, request, pk=None):
        logger.debug(f'Acessando cronômetro do evento: {pk}')
        evento = self.get_object()
        cronometro, created = evento.get_or_create_unique_cronometro()
        sleep(1)
        if cronometro:
            if not evento.start_real and cronometro.started_at and not cronometro.finished_at:
                evento.start_real = cronometro.started_at
                evento.save(update_fields=['start_real'])
            if not evento.end_real and cronometro.finished_at:
                evento.end_real = cronometro.finished_at
                evento.save(update_fields=['end_real'])

            return Response(CronometroTreeSerializer(cronometro).data)
        return Response({'error': 'Cronometro not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['PATCH'], permission_classes=[EventoChangePermission])
    def finish(self, request, pk=None):
        logger.debug(f'Finalizando Evento: {pk}')
        evento = self.get_object()
        cronometro, created = evento.get_or_create_unique_cronometro()
        if cronometro:
            cronometro_manager.stop_cronometro(cronometro.id)
            cronometro_manager.finish_cronometro(cronometro.id)
            cronometro.refresh_from_db()
            if not evento.end_real and cronometro.finished_at:
                evento.end_real = cronometro.finished_at
                evento.save(update_fields=['end_real'])

            for ind in evento.individuos.all():
                cron, created = ind.get_or_create_unique_cronometro()
                if cron and cron.state != CronometroState.STOPPED:
                    cronometro_manager.stop_cronometro(cron.id)
                    cronometro_manager.finish_cronometro(cron.id)
                ind.status_microfone = False
                ind.com_a_palavra = False
                ind.aparteante = None
                ind.save(update_fields=['status_microfone', 'com_a_palavra', 'aparteante'])

            return Response(EventoSerializer(evento).data)
        return Response({'error': 'Cronometro not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['PATCH'], permission_classes=[EventoChangePermission])
    def copy(self, request, *args, **kwargs):
        evento_copiado = self.get_object()
        if not evento_copiado.end_real:
            return Response({'error': 'Evento não finalizado. Só é possível copiar eventos finalizados.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            evento = Evento.objects.create(
                name=f'{evento_copiado.name}',
                start_previsto=timezone.now(),
                start_real=None,
                end_real=None,
                duration=evento_copiado.duration,
                ips_mesas=evento_copiado.ips_mesas,
                youtube_id='',
                comunicar_com_mesas=evento_copiado.comunicar_com_mesas,
                description=f'Copia gerada a partir do evento {evento_copiado.name} '
                f'de {formats.date_format(timezone.localtime(evento_copiado.start_real), "d/m/Y - H:i")}',
            )

            for individuo in evento_copiado.individuos.all():
                individuo.pk = None
                individuo.evento = evento
                individuo.status_microfone = False
                individuo.com_a_palavra = False
                individuo.aparteante = None
                individuo.save()

            for painel in evento_copiado.paineis.all():
                painel.copy(evento=evento, sessao=None)

        return Response(EventoSerializer(evento).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['PATCH'], permission_classes=[EventoChangePermission])
    def toggle_microfones(self, request, *args, **kwargs):
        status_microfone = request.data.get('status_microfone', 'on')
        inclui_microfone_sempre_ativo = request.data.get('inclui_microfone_sempre_ativo', 'off')
        if inclui_microfone_sempre_ativo not in ['on', 'off']:
            inclui_microfone_sempre_ativo = 'off'
        if status_microfone not in ['on', 'off']:
            status_microfone = 'off'
        evento = self.get_object()
        logger.debug(f'Toggle microfones do evento {evento} para {status_microfone}')

        for individuo in evento.individuos.all():
            if individuo.microfone_sempre_ativo and inclui_microfone_sempre_ativo == 'off':
                logger.debug(f'  Individuo {individuo} tem microfone sempre ativo, pulando')
                continue
            logger.debug(f'  Toggle microfone {individuo} para {status_microfone}')
            individuo.status_microfone = status_microfone == 'on'
            individuo.auto_corte_microfone = False
            individuo.com_a_palavra = False
            individuo.aparteante = None
            update_fields = ['status_microfone', 'com_a_palavra', 'aparteante']
            individuo.save(update_fields=update_fields)
            if status_microfone == 'off':
                cron, created = individuo.get_or_create_unique_cronometro()
                cronometro_manager.stop_cronometro(cron.id)

        if SEND_MESSAGE_MICROPHONE or not settings.DEBUG:
            clients = {}
            for individuo in evento.individuos.all():
                ips_mesas = individuo.ips
                for ip in ips_mesas:
                    if ip not in clients:
                        try:
                            porta = 10023
                            client = udp_client.SimpleUDPClient(ip, porta)
                            client.send_message("/xremote", None)
                            clients[ip] = client
                        except Exception as e:
                            logger.error(f'Erro ao criar cliente OSC para o IP {ip}: {e}')

            for individuo in evento.individuos.all():
                for ip in individuo.ips:
                    client = clients.get(ip)
                    if client:
                        client.send_message(f"/ch/{individuo.channel_display}/mix/on", 1 if status_microfone == 'on' else 0)

        return Response({'status': 'ok', 'status_microfone': status_microfone, 'evento': evento.id})

    @action(detail=True, methods=['PATCH'], permission_classes=[EventoChangePermission])
    def pause_parent_on_aparte(self, request, *args, **kwargs):
        pause_parent_on_aparte = request.data.get('pause_parent_on_aparte', 'on')
        evento = self.get_object()

        cron, created = evento.get_or_create_unique_cronometro()
        if cron:
            cron.pause_parent_on_start = True if pause_parent_on_aparte == 'on' else False
            cron.save(update_fields=['pause_parent_on_start'])

        for individuo in evento.individuos.all():
            cronometro, created = individuo.get_or_create_unique_cronometro()
            cronometro.pause_parent_on_start = True if pause_parent_on_aparte == 'on' else False
            cronometro.save(update_fields=['pause_parent_on_start'])

        return Response(
            {'status': 'ok',
             'evento': evento.id,
             'pause_parent_on_aparte': cronometro.pause_parent_on_start
            })

    @action(detail=True, methods=['patch'])
    def reset_to_defaults(self, request, pk=None):
        evento = self.get_object()
        evento.reset_to_defaults()
        return Response({'status': 'ok', 'evento': evento.id})



@customize(Individuo)
class _IndividuoViewSet(ResponseFileMixin):
    serializer_class = IndividuoSerializer

    @action(detail = True)
    def fotografia(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)

    @action(detail=True, methods=['POST'])
    def change_position(self, request, *args, **kwargs):
        result = {
            'status': 200,
            'message': 'OK'
        }
        d = request.data
        if 'pos_ini' in d and 'pos_fim' in d:
            if d['pos_ini'] != d['pos_fim']:
                pk = kwargs['pk']
                Individuo.objects.reposicione(pk, d['pos_fim'])

        return Response(result)


    @action(detail=True, methods=['PATCH'], permission_classes=[EventoChangePermission])
    def force_stop_cronometro(self, request, *args, **kwargs):
        cronometro_manager = CronometroManager()
        individuo = self.get_object()
        logger.debug(f'Forçando stop do cronometro do indivíduo {individuo}: status_microfone {individuo.status_microfone}, com_a_palavra={individuo.com_a_palavra}')
        cron, created = individuo.get_or_create_unique_cronometro()
        if cron.state != CronometroState.STOPPED:
            cronometro_manager.stop_cronometro(cron.id)
        return Response(
            {'status': 'ok',
             'individuo': individuo.id
            }
        )

    @action(detail=True, methods=['PATCH'], permission_classes=[EventoChangePermission])
    def toggle_aparteante(self, request, *args, **kwargs):
        cronometro_manager = CronometroManager()
        individuoAparteante = self.get_object()

        aparteante_status = request.data.get('aparteante_status', 0)
        if aparteante_status not in [0, 1]:
            aparteante_status = 0
        aparteante_status = aparteante_status == 1

        default_timer = request.data.get('default_timer', 60)  # em segundos
        try:
            default_timer = int(default_timer)
            default_timer = timedelta(
                seconds=default_timer,
                microseconds=300_000
            )
        except ValueError:
            default_timer = timedelta(seconds=60, microseconds=300_000)

        logger.debug(f'timer: {default_timer} Toggle aparteante {individuoAparteante}: status_microfone {individuoAparteante.status_microfone}, com_a_palavra={individuoAparteante.com_a_palavra}')

        individuoComPalavra = individuoAparteante.evento.individuos.filter(com_a_palavra=True).first()

        if not individuoComPalavra:
            raise DRFValidationError('A palavra não está sendo utilizada. Não é possível fazer aparte.')
        else:

            if individuoComPalavra.id == individuoAparteante.id:
                # Ele mesmo está com a palavra, nada a fazer
                logger.debug(f'  Indivíduo {individuoAparteante} já está com a palavra, nada a fazer')
                return Response(
                    {'status': 'ok',
                     'individuo': individuoAparteante.id
                     })
            else:
                antigoAparteante = individuoComPalavra.aparteante

                if antigoAparteante:
                    individuoComPalavra.aparteante = None
                    individuoComPalavra.save(update_fields=['aparteante'])
                    cron, created = antigoAparteante.get_or_create_unique_cronometro()
                    cron.parent = None
                    cron.save()
                    antigoAparteante.save()
                    cronometro_manager.stop_cronometro(cron.id)

                cronAparteante, created = individuoAparteante.get_or_create_unique_cronometro()
                cronAparteado, created = individuoComPalavra.get_or_create_unique_cronometro()

                if not aparteante_status:
                    # Ele não está com a palavra, e quer desligar o aparteante
                    logger.debug(f'  Indivíduo {individuoAparteante} não está com a palavra, e quer se desligar do aparteante. Desligando aparte.')
                    individuoComPalavra.aparteante = None
                    individuoComPalavra.save(update_fields=['aparteante'])
                    individuoAparteante.save()
                    cronometro_manager.stop_cronometro(cronAparteante.id)
                    cronometro_manager.resume_cronometro(cronAparteado.id)
                else:
                    # Ele não está com a palavra, mas outro indivíduo está
                    logger.debug(f'  Indivíduo {individuoAparteante} não está com a palavra, mas o indivíduo {individuoComPalavra} está. Permitindo aparte.')
                    cronometro_manager.start_cronometro(cronAparteante.id, cronAparteado.id, duration=default_timer)
                    individuoComPalavra.aparteante = individuoAparteante
                    individuoComPalavra.save(update_fields=['aparteante'])
                    individuoAparteante.save()

                    # Iniciar cronômetro do aparteante não é necessário, pois ele é CronometroPalavra chama ele como auto_start
                    # cronometro_manager.start_cronometro(cronAparteante.id, cronAparteado.id, duration=default_timer)

        return Response(
            {'status': 'ok',
             'individuo': individuoAparteante.id
             })

    @action(detail=True, methods=['PATCH'], permission_classes=[EventoChangePermission])
    def toggle_microfone(self, request, *args, **kwargs):

        cronometro_manager = CronometroManager()

        individuo = self.get_object()
        mic_old = {'order': individuo.channel_display, 'status_microfone': 'on' if individuo.status_microfone else 'off'}
        # obter status_microfone e com_a_palavra de todos os individuos do evento
        #microfones_do_evento = list(individuo.evento.individuos.values('order', 'status_microfone'))

        logger.debug(f'Toggle microfone {individuo.id} - {individuo}: status_microfone {individuo.status_microfone}, com_a_palavra={individuo.com_a_palavra}')
        status_microfone = request.data.get('status_microfone', 'on')
        com_a_palavra = request.data.get('com_a_palavra', 0)
        default_timer = request.data.get('default_timer', 300)  # em segundos
        try:
            default_timer = int(default_timer)
            micro = min(default_timer * 1_000, 300_000)
            default_timer = timedelta(
                seconds=default_timer,
                microseconds=micro
            )
        except ValueError:
            default_timer = timedelta(seconds=300, microseconds=300_000)

        logger.debug(f'  timer: {default_timer}: status_microfone={status_microfone}, com_a_palavra={com_a_palavra}')

        if com_a_palavra not in [0, 1, '0', '1']:
            com_a_palavra = 0
        if status_microfone not in ['on', 'off']:
            status_microfone = 'off'

        if com_a_palavra == 1:
            # Remover com_a_palavra de todos os outros individuos do evento
            ind_com_a_palavra = individuo.evento.individuos.filter(com_a_palavra=True).exclude(id=individuo.id)
            for ind in ind_com_a_palavra:
                cronAparteado, created = ind.get_or_create_unique_cronometro()

                aparteante = ind.aparteante

                ind.auto_corte_microfone = False
                ind.aparteante = None
                ind.com_a_palavra = False
                ind.save()

                if aparteante:
                    cronAparteante, created = aparteante.get_or_create_unique_cronometro()
                    aparteante.save()
                    cronometro_manager.stop_cronometro(cronAparteante.id)

                cronometro_manager.stop_cronometro(cronAparteado.id)


            # Se houver apenas mais um individuo com microfone ligado, desligar o microfone dele se ele não tiver microfone sempre ativo
            ind_mic_ligado = individuo.evento.individuos.filter(
                status_microfone=True,
                microfone_sempre_ativo=False
                ).exclude(id=individuo.id)
            if ind_mic_ligado.count() == 1:
                outro = ind_mic_ligado.first()
                if outro:
                    outro.status_microfone = False
                    outro.com_a_palavra = False
                    outro.auto_corte_microfone = False
                    outro.save()

        individuo.status_microfone = True if status_microfone == 'on' else False
        #individuo.com_a_palavra = True if com_a_palavra == 1 and individuo.status_microfone else False
        individuo.com_a_palavra = True if com_a_palavra == 1 else False

        aparteante = individuo.aparteante
        if not individuo.com_a_palavra and aparteante:
            individuo.aparteante = None
            aparteante.save()
            cron, created = aparteante.get_or_create_unique_cronometro()
            cronometro_manager.stop_cronometro(cron.id)

        cron, created = individuo.get_or_create_unique_cronometro()
        individuo.save()
        if individuo.com_a_palavra:
            if individuo.status_microfone:
                if cron.state == CronometroState.PAUSED:
                    cronometro_manager.resume_cronometro(cron.id)
                else:
                    cronometro_manager.start_cronometro(cron.id, duration=default_timer)
            else:
                cronometro_manager.pause_cronometro(cron.id)
        else:
            if hasattr(individuo, 'aparteado') and individuo.aparteado:
                if individuo.status_microfone:
                    if cron.state == CronometroState.PAUSED:
                        cronometro_manager.resume_cronometro(cron.id)
                    else:
                        cronometro_manager.start_cronometro(cron.id, duration=default_timer)
                else:
                    cronometro_manager.pause_cronometro(cron.id)
            else:
                cronometro_manager.stop_cronometro(cron.id)


        # obter status_microfone e com_a_palavra de todos os individuos do evento
        microfones_do_evento_depois = list(individuo.evento.individuos.values('order', 'status_microfone'))
        #logger.debug(f'  Microfones do evento antes: {list(microfones_do_evento)}')
        #logger.debug(f'  Microfones do evento depois: {list(microfones_do_evento_depois)}')

        # Enviar comando OSC para a mesa de som dos microfones que mudaram de estado
        #microfones_mudaram = []
        #for antes, depois in zip(microfones_do_evento, microfones_do_evento_depois):
        #    if antes['status_microfone'] != depois['status_microfone']:
        #        microfones_mudaram.append(depois)
        #        logger.debug(f'  Microfone {antes["order"]} mudou : {antes["status_microfone"]} -> {depois["status_microfone"]}')

        mic = {'order': individuo.channel_display, 'status_microfone': 'on' if individuo.status_microfone else 'off'}
        if mic != mic_old:
            logger.debug(f'Enviando comando OSC para o microfone {mic["order"]}: status_microfone={mic["status_microfone"]}')
            if SEND_MESSAGE_MICROPHONE or not settings.DEBUG:
                ips_mesas = individuo.ips
                for ip in ips_mesas:
                    try:
                        porta = 10023
                        client = udp_client.SimpleUDPClient(ip, porta)
                        client.send_message("/xremote", None)
                        client.send_message(f"/ch/{mic['order']}/mix/on", 1 if mic["status_microfone"] == 'on' else 0)
                    except Exception as e:
                        logger.error(f'Erro ao enviar comando OSC para o microfone {mic["order"]} no IP {ip}: {e}')

        #for mic in microfones_mudaram:
        #    logger.debug(f'  Enviando comando OSC para o microfone {mic["order"]}: status_microfone={mic["status_microfone"]}')
        #    if not settings.DEBUG:

        return Response(
            {'status': 'ok',
             'status_microfone': status_microfone,
             'individuo': individuo.id
             })

@customize(Cronometro)
class _CronometroViewSet:
    serializer_class = CronometroSerializer

    def perform_create(self, serializer):
        """Criar cronômetro usando o CronometroManager"""
        cronometro = serializer.save()
        # Notificar observers sobre criação
        cronometro_manager.notify_observers(cronometro, 'created')

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Iniciar cronômetro usando o CronometroManager"""
        result = cronometro_manager.start_cronometro(pk)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pausar cronômetro usando o CronometroManager"""
        result = cronometro_manager.pause_cronometro(pk)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Parar cronômetro usando o CronometroManager"""
        result = cronometro_manager.stop_cronometro(pk)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Retomar cronômetro usando o CronometroManager"""
        result = cronometro_manager.resume_cronometro(pk)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Obter árvore de cronômetros usando o CronometroManager"""
        tree_data = cronometro_manager.get_cronometro_tree(pk)
        if tree_data:
            return Response(tree_data)
        return Response({'error': 'Cronometro not found'}, status=status.HTTP_404_NOT_FOUND)


@customize(VisaoDePainel)
class _VisaoDePainelViewSet:
    @action(detail=True, methods=['patch'])
    def activate(self, request, pk=None):
        visao = self.get_object()
        visao.activate()
        return Response({'status': 'ok', 'visao': visao.id})


@customize(Painel)
class _PainelViewSet:

    @classmethod
    def build(cls, **kwargs):
        class PainelSerializer(cls.serializer_class):
            visao_ativa = serializers.IntegerField(read_only=True)

        cls.serializer_class = PainelSerializer
        return cls
