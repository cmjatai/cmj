
from django.utils import timezone
from datetime import timedelta

from cmj.api.serializers_painelset import CronometroSerializer, CronometroTreeSerializer
from .models import Cronometro, CronometroState
from .cronometro_commands import (
    AddTimeCronometroCommand, StartCronometroCommand, PauseCronometroCommand,
    ResumeCronometroCommand, StopCronometroCommand, FinishCronometroCommand
)

class CronometroManager:
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

    def notify_observers(self, cronometro, event_type, data=None):
        """Notifica todos os observadores sobre eventos do cronômetro"""
        for observer in self._observers:
            observer.update(cronometro, event_type, data)

    def create_cronometro(self, name, duration, parent_id=None, **kwargs):
        """Cria um novo cronômetro"""
        parent = None
        if parent_id:
            try:
                parent = Cronometro.objects.get(id=parent_id)
            except Cronometro.DoesNotExist:
                return {"error": "Cronômetro pai não encontrado"}

        cronometro = Cronometro.objects.create(
            name=name,
            duration=duration,
            parent=parent,
            **kwargs
        )

        self.notify_observers(cronometro, 'created')
        return {"success": True, "cronometro_id": cronometro.id}

    def start_cronometro(self, cronometro_id, parent_id=None, duration=None):
        """Inicia um cronômetro usando Command Pattern"""
        command = StartCronometroCommand(cronometro_id, parent_id=parent_id, duration=duration)
        result = command.execute()

        if result.get('success'):
            self.notify_observers(command.cronometro, 'started')

        return result

    def pause_cronometro(self, cronometro_id):
        """Pausa um cronômetro"""
        command = PauseCronometroCommand(cronometro_id)
        result = command.execute()

        if result.get('success'):
            self.notify_observers(command.cronometro, 'paused')

        return result

    def resume_cronometro(self, cronometro_id):
        """Retoma um cronômetro pausado"""
        command = ResumeCronometroCommand(cronometro_id)
        result = command.execute()

        if result.get('success'):
            self.notify_observers(command.cronometro, 'resumed')

        return result

    def stop_cronometro(self, cronometro_id):
        """Para um cronômetro"""
        command = StopCronometroCommand(cronometro_id)
        result = command.execute()

        if result.get('success'):
            self.notify_observers(command.cronometro, 'stopped')

        return result

    def add_time(self, cronometro_id, seconds):
        command = AddTimeCronometroCommand(cronometro_id, seconds)
        result = command.execute()

        if result.get('success'):
            self.notify_observers(command.cronometro, 'time_added')

        return result

    def check_finished_cronometros(self):
        """
        Verifica cronômetros que podem ter terminado
        Chamado periodicamente por uma tarefa em background
        """
        running_cronometros = Cronometro.objects.filter(state=CronometroState.RUNNING)
        finished_cronometros = []

        for cronometro in running_cronometros:
            if cronometro.remaining_time <= timedelta():
                command = FinishCronometroCommand(cronometro.id)
                result = command.execute()

                if result.get('success'):
                    finished_cronometros.append(command.cronometro)
                    self.notify_observers(command.cronometro, 'finished')

        return finished_cronometros

    def get_cronometro_data(self, cronometro):
        """
        Retorna os dados de um cronômetro e seus descendentes em formato serializado
        """
        try:
            if not isinstance(cronometro, Cronometro):
                cronometro = Cronometro.objects.get(id=cronometro)
            return {
                "cronometro": CronometroTreeSerializer(cronometro).data
            }
        except Cronometro.DoesNotExist:
            return None


# Observer concreto para logging
class CronometroLogger:
    """Observer concreto para registrar eventos de cronômetros"""

    def update(self, cronometro, event_type, data=None):
        print(f"[Cronometro Log] {cronometro.name}: {event_type} at {timezone.now()}")
        if data:
            print(f"  Data: {data}")

# Observer concreto para métricas
class CronometroMetrics:
    """Observer concreto para coletar métricas de cronômetros"""

    def __init__(self):
        self.metrics = {}

    def update(self, cronometro, event_type, data=None):
        cronometro_id = str(cronometro.id)
        if cronometro_id not in self.metrics:
            self.metrics[cronometro_id] = {
                'starts': 0,
                'pauses': 0,
                'resumes': 0,
                'stops': 0,
                'finishes': 0
            }

        if event_type in self.metrics[cronometro_id]:
            self.metrics[cronometro_id][event_type] += 1