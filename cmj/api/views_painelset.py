import logging

from django.apps.registry import apps

from cmj.api.serializers_painelset import CronometroSerializer, EventoSerializer
from cmj.painelset.cronometro_manager import CronometroManager
from cmj.painelset.models import Cronometro, Evento, Individuo
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status

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
    def cronometro(self, request, pk=None):
        evento = self.get_object()
        cronometro = evento.get_or_create_unique_cronometro()
        if cronometro:
            serializer = CronometroSerializer(cronometro)
            return Response(serializer.data)
        return Response({'error': 'Cronometro not found'}, status=status.HTTP_404_NOT_FOUND)

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
