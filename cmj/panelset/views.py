
# timer_app/views.py - Views da aplicação
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Timer
from .serializers import TimerSerializer, TimerTreeSerializer
from .timer_manager import TimerManager

# Manager global (em produção, usar dependency injection)
timer_manager = TimerManager()

class TimerViewSet(viewsets.ModelViewSet):
    """ViewSet para operações CRUD de cronômetros"""
    queryset = Timer.objects.all()
    serializer_class = TimerSerializer

    def perform_create(self, serializer):
        """Criar cronômetro usando o TimerManager"""
        timer = serializer.save()
        # Notificar observers sobre criação
        timer_manager.notify_observers(timer, 'created')

# Views para operações de cronômetro
@api_view(['POST'])
def start_timer(request, timer_id):
    """Iniciar cronômetro"""
    result = timer_manager.start_timer(timer_id)
    return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def pause_timer(request, timer_id):
    """Pausar cronômetro"""
    result = timer_manager.pause_timer(timer_id)
    return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def resume_timer(request, timer_id):
    """Retomar cronômetro"""
    result = timer_manager.resume_timer(timer_id)
    return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def stop_timer(request, timer_id):
    """Parar cronômetro"""
    result = timer_manager.stop_timer(timer_id)
    return Response(result, status=status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def timer_tree(request, timer_id):
    """Obter árvore de cronômetros"""
    tree_data = timer_manager.get_timer_tree(timer_id)
    if tree_data:
        return Response(tree_data)
    return Response({'error': 'Timer not found'}, status=status.HTTP_404_NOT_FOUND)

# Views para interface web
def timer_dashboard(request):
    """Dashboard principal"""
    root_timers = Timer.objects.filter(parent=None)
    return render(request, 'panelset/dashboard.html', {
        'root_timers': root_timers
    })

def timer_detail(request, timer_id):
    """Detalhes de um cronômetro"""
    timer = get_object_or_404(Timer, id=timer_id)
    tree_data = timer_manager.get_timer_tree(timer_id)
    return render(request, 'panelset/timer_detail.html', {
        'timer': timer,
        'tree_data': tree_data
    })
