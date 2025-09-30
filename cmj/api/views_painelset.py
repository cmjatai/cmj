import logging

from django.apps.registry import apps

from cmj.painelset.models import Individuo
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



'''''
timer_manager = TimerManager()

@customize(Timer)
class _TimerViewSet:
    serializer_class = TimerSerializer

    def perform_create(self, serializer):
        """Criar cronômetro usando o TimerManager"""
        timer = serializer.save()
        # Notificar observers sobre criação
        timer_manager.notify_observers(timer, 'created')

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Iniciar cronômetro usando o TimerManager"""
        result = timer_manager.start_timer(pk)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pausar cronômetro usando o TimerManager"""
        result = timer_manager.pause_timer(pk)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Parar cronômetro usando o TimerManager"""
        result = timer_manager.stop_timer(pk)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Retomar cronômetro usando o TimerManager"""
        result = timer_manager.resume_timer(pk)
        return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Obter árvore de cronômetros usando o TimerManager"""
        tree_data = timer_manager.get_timer_tree(pk)
        if tree_data:
            return Response(tree_data)
        return Response({'error': 'Timer not found'}, status=status.HTTP_404_NOT_FOUND)

'''