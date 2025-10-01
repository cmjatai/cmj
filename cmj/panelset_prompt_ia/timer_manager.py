
from django.utils import timezone
from datetime import timedelta
from .models import Timer, TimerState
from .timer_commands import (
    StartTimerCommand, PauseTimerCommand,
    ResumeTimerCommand, StopTimerCommand, FinishTimerCommand
)

class TimerManager:
    """
    Mediator Pattern: Classe central para coordenar operações de cronômetros
    Observer Pattern: Gerencia notificações para observadores registrados
    """

    def __init__(self):
        self._observers = []

    def add_observer(self, observer):
        """Adiciona observador (Observer Pattern)"""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        """Remove observador"""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, timer, event_type, data=None):
        """Notifica todos os observadores sobre eventos do cronômetro"""
        for observer in self._observers:
            observer.update(timer, event_type, data)

    def create_timer(self, name, duration, parent_id=None, **kwargs):
        """Cria um novo cronômetro"""
        parent = None
        if parent_id:
            try:
                parent = Timer.objects.get(id=parent_id)
            except Timer.DoesNotExist:
                return {"error": "Cronômetro pai não encontrado"}

        timer = Timer.objects.create(
            name=name,
            duration=duration,
            parent=parent,
            **kwargs
        )

        self.notify_observers(timer, 'created')
        return {"success": True, "timer_id": timer.id}

    def start_timer(self, timer_id):
        """Inicia um cronômetro usando Command Pattern"""
        command = StartTimerCommand(timer_id)
        result = command.execute()

        if result.get('success'):
            timer = Timer.objects.get(id=timer_id)
            self.notify_observers(timer, 'started')

        return result

    def pause_timer(self, timer_id):
        """Pausa um cronômetro"""
        command = PauseTimerCommand(timer_id)
        result = command.execute()

        if result.get('success'):
            timer = Timer.objects.get(id=timer_id)
            self.notify_observers(timer, 'paused')

        return result

    def resume_timer(self, timer_id):
        """Retoma um cronômetro pausado"""
        command = ResumeTimerCommand(timer_id)
        result = command.execute()

        if result.get('success'):
            timer = Timer.objects.get(id=timer_id)
            self.notify_observers(timer, 'resumed')

        return result

    def stop_timer(self, timer_id):
        """Para um cronômetro"""
        command = StopTimerCommand(timer_id)
        result = command.execute()

        if result.get('success'):
            timer = Timer.objects.get(id=timer_id)
            self.notify_observers(timer, 'stopped')

        return result

    def check_finished_timers(self):
        """
        Verifica cronômetros que podem ter terminado
        Chamado periodicamente por uma tarefa em background
        """
        running_timers = Timer.objects.filter(state=TimerState.RUNNING)
        finished_timers = []

        for timer in running_timers:
            if timer.remaining_time <= timedelta():
                command = FinishTimerCommand(timer.id)
                result = command.execute()

                if result.get('success'):
                    finished_timers.append(timer)
                    self.notify_observers(timer, 'finished')

        return finished_timers

    def get_timer_tree(self, root_timer_id):
        """
        Retorna uma árvore hierárquica de cronômetros
        Composite Pattern: navega pela estrutura hierárquica
        """
        try:
            root = Timer.objects.get(id=root_timer_id)
        except Timer.DoesNotExist:
            return None

        def build_tree_node(timer):
            return {
                'id': str(timer.id),
                'name': timer.name,
                'state': timer.state,
                'duration': timer.duration.total_seconds(),
                'elapsed_time': timer.elapsed_time.total_seconds(),
                'remaining_time': timer.remaining_time.total_seconds(),
                'pause_parent_on_start': timer.pause_parent_on_start,
                'children': [build_tree_node(child) for child in timer.get_children()]
            }

        return build_tree_node(root)

# Observer concreto para logging
class TimerLogger:
    """Observer concreto para registrar eventos de cronômetros"""

    def update(self, timer, event_type, data=None):
        print(f"[Timer Log] {timer.name}: {event_type} at {timezone.now()}")
        if data:
            print(f"  Data: {data}")

# Observer concreto para métricas
class TimerMetrics:
    """Observer concreto para coletar métricas de cronômetros"""

    def __init__(self):
        self.metrics = {}

    def update(self, timer, event_type, data=None):
        timer_id = str(timer.id)
        if timer_id not in self.metrics:
            self.metrics[timer_id] = {
                'starts': 0,
                'pauses': 0,
                'resumes': 0,
                'stops': 0,
                'finishes': 0
            }

        if event_type in self.metrics[timer_id]:
            self.metrics[timer_id][event_type] += 1