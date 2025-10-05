import logging

from django.apps.registry import apps
from django.conf import settings

from cmj.api.serializers_painelset import CronometroSerializer, CronometroTreeSerializer, EventoSerializer
from cmj.painelset.cronometro_manager import CronometroManager
from cmj.painelset.models import Cronometro, Evento, Individuo
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status

from pythonosc import udp_client


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('painelset')
    ]
)

cronometro_manager = CronometroManager()

@customize(Evento)
class _EventoViewSet:
    serializer_class = EventoSerializer
    @action(detail=True, methods=['GET'])
    def start(self, request, pk=None):
        print('Acessando cronômetro do evento:', pk)
        evento = self.get_object()
        cronometro, created = evento.get_or_create_unique_cronometro()
        if cronometro:
            if not evento.start_real and cronometro.started_at and not cronometro.finished_at:
                evento.start_real = cronometro.started_at
                evento.save(update_fields=['start_real'])
            if not evento.end_real and cronometro.finished_at:
                evento.end_real = cronometro.finished_at
                evento.save(update_fields=['end_real'])
            return Response(CronometroTreeSerializer(cronometro).data)
        return Response({'error': 'Cronometro not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['GET'])
    def toggle_microfones(self, request, *args, **kwargs):
        status_microfone = request.GET.get('status_microfone', 'on')
        evento = self.get_object()
        print(f'Toggle microfones do evento {evento} para {status_microfone}')

        if not settings.DEBUG:
            ip = "10.3.163.49"  # Substitua pelo endereço IP da sua mesa
            porta = 10023
            client = udp_client.SimpleUDPClient(ip, porta)
            client.send_message("/xremote", None)

        for individuo in evento.individuos.all():
            print(f'  Toggle microfone {individuo} para {status_microfone}')
            individuo.status_microfone = status_microfone == 'on'
            individuo.com_a_palavra = status_microfone == 'on' and individuo.com_a_palavra
            update_fields = ['status_microfone', 'com_a_palavra']
            individuo.save(update_fields=update_fields)
            if not settings.DEBUG:
                client.send_message(f"/ch/{evento.order:>02}/mix/on", 1 if status_microfone == 'on' else 0)

        return Response({'status': 'ok', 'status_microfone': status_microfone, 'evento': evento.id})

@customize(Individuo)
class _IndividuoViewSet:

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

    @action(detail=True, methods=['GET'])
    def toggle_microfone(self, request, *args, **kwargs):

        individuo = self.get_object()
        mic_old = {'order': individuo.order, 'status_microfone': 'on' if individuo.status_microfone else 'off'}
        # obter status_microfone e com_a_palavra de todos os individuos do evento
        #microfones_do_evento = list(individuo.evento.individuos.values('order', 'status_microfone'))

        print(f'Toggle microfone {individuo.id} - {individuo}: status_microfone {individuo.status_microfone}, com_a_palavra={individuo.com_a_palavra}')
        status_microfone = request.GET.get('status_microfone', 'on')
        com_a_palavra = request.GET.get('com_a_palavra', '0')
        print(f'  Para: status_microfone={status_microfone}, com_a_palavra={com_a_palavra}')

        if com_a_palavra not in ['0', '1']:
            com_a_palavra = '0'
        if status_microfone not in ['on', 'off']:
            status_microfone = 'off'

        if individuo.microfone_sempre_ativo:
            mic_old = {}
            if com_a_palavra == '1':
                # Remover com_a_palavra de todos os outros individuos do evento
                ind_com_a_palavra = individuo.evento.individuos.filter(com_a_palavra=True).exclude(id=individuo.id)
                for ind in ind_com_a_palavra:
                    ind.com_a_palavra = False
                    ind.save(update_fields=['com_a_palavra'])

                individuo.status_microfone = True
                individuo.com_a_palavra = True
                individuo.save(update_fields=['status_microfone', 'com_a_palavra'])
                logger.debug(f'  Indivíduo {individuo} tem microfone sempre ativo. Forçando status_microfone=on e com_a_palavra=1')
            else:
                individuo.status_microfone = True
                individuo.com_a_palavra = False
                individuo.save(update_fields=['status_microfone', 'com_a_palavra'])
                logger.debug(f'  Indivíduo {individuo} tem microfone sempre ativo. Forçando status_microfone=on e com_a_palavra=0')

        else:
            if com_a_palavra == '1':
                # Remover com_a_palavra de todos os outros individuos do evento
                ind_com_a_palavra = individuo.evento.individuos.filter(com_a_palavra=True).exclude(id=individuo.id)
                for ind in ind_com_a_palavra:
                    ind.com_a_palavra = False
                    ind.save(update_fields=['com_a_palavra'])

                ind_mic_ligado = individuo.evento.individuos.filter(
                    status_microfone=True, microfone_sempre_ativo=False
                    ).exclude(id=individuo.id)
                if ind_mic_ligado.count() == 1:
                    # Se houver apenas mais um individuo com microfone ligado, desligar o microfone dele se ele não tiver microfone sempre ativo
                    outro = ind_mic_ligado.first()
                    if outro:
                        outro.status_microfone = False
                        outro.com_a_palavra = False
                        outro.save(update_fields=['status_microfone', 'com_a_palavra'])
            individuo.status_microfone = True if status_microfone == 'on' else False
            individuo.com_a_palavra = True if com_a_palavra == '1' and individuo.status_microfone else False
            individuo.save(update_fields=['status_microfone', 'com_a_palavra'])

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

        mic = {'order': individuo.order, 'status_microfone': 'on' if individuo.status_microfone else 'off'}
        if mic != mic_old:
            logger.debug(f'Enviando comando OSC para o microfone {mic["order"]}: status_microfone={mic["status_microfone"]}')
            if not settings.DEBUG:
                ip = "10.3.163.49"  # Substitua pelo endereço IP da sua mesa
                porta = 10023
                client = udp_client.SimpleUDPClient(ip, porta)
                client.send_message("/xremote", None)
                client.send_message(f"/ch/{mic['order']:>02}/mix/on", 1 if mic["status_microfone"] == 'on' else 0)

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
