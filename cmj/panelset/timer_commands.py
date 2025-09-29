
from abc import ABC, abstractmethod
from django.utils import timezone
from datetime import timedelta
from .models import Timer, TimerState, TimerEvent

class TimerCommand(ABC):
    """
    Command Pattern: Interface base para comandos de cronômetro
    """

    def __init__(self, timer_id):
        self.timer_id = timer_id
        self.timer = None

    def execute(self):
        """Executa o comando"""
        try:
            self.timer = Timer.objects.get(id=self.timer_id)
            return self._execute_command()
        except Timer.DoesNotExist:
            return {"error": "Cronômetro não encontrado"}

    @abstractmethod
    def _execute_command(self):
        """Implementação específica do comando"""
        pass

class StartTimerCommand(TimerCommand):
    """Comando para iniciar cronômetro"""

    def _execute_command(self):
        if self.timer.state != TimerState.STOPPED:
            return {"error": "Cronômetro já está em execução ou pausado"}

        self.timer.state = TimerState.RUNNING
        self.timer.started_at = timezone.now()
        self.timer.accumulated_time = timedelta()
        self.timer.save()

        # Criar evento
        TimerEvent.objects.create(
            timer=self.timer,
            event_type='started'
        )

        return {"success": True, "message": "Cronômetro iniciado"}

class PauseTimerCommand(TimerCommand):
    """Comando para pausar cronômetro"""

    def _execute_command(self):
        if self.timer.state != TimerState.RUNNING:
            return {"error": "Cronômetro não está em execução"}

        # Acumular tempo decorrido
        if self.timer.started_at:
            elapsed = timezone.now() - self.timer.started_at
            self.timer.accumulated_time += elapsed

        self.timer.state = TimerState.PAUSED
        self.timer.paused_at = timezone.now()
        self.timer.save()

        # Criar evento
        TimerEvent.objects.create(
            timer=self.timer,
            event_type='paused'
        )

        return {"success": True, "message": "Cronômetro pausado"}

class ResumeTimerCommand(TimerCommand):
    """Comando para retomar cronômetro pausado"""

    def _execute_command(self):
        if self.timer.state != TimerState.PAUSED:
            return {"error": "Cronômetro não está pausado"}

        self.timer.state = TimerState.RUNNING
        self.timer.started_at = timezone.now()
        self.timer.paused_at = None
        self.timer.save()

        # Criar evento
        TimerEvent.objects.create(
            timer=self.timer,
            event_type='resumed'
        )

        return {"success": True, "message": "Cronômetro retomado"}

class StopTimerCommand(TimerCommand):
    """Comando para parar cronômetro"""

    def _execute_command(self):
        if self.timer.state == TimerState.STOPPED:
            return {"error": "Cronômetro já está parado"}

        # Parar cronômetros filhos primeiro
        for child in self.timer.get_children():
            if child.state in [TimerState.RUNNING, TimerState.PAUSED]:
                StopTimerCommand(child.id).execute()

        self.timer.state = TimerState.STOPPED
        self.timer.started_at = None
        self.timer.paused_at = None
        self.timer.accumulated_time = timedelta()
        self.timer.save()

        # Criar evento
        TimerEvent.objects.create(
            timer=self.timer,
            event_type='stopped'
        )

        return {"success": True, "message": "Cronômetro parado"}

class FinishTimerCommand(TimerCommand):
    """Comando para finalizar cronômetro (quando tempo acaba)"""

    def _execute_command(self):
        if self.timer.state != TimerState.RUNNING:
            return {"error": "Cronômetro não está em execução"}

        self.timer.state = TimerState.FINISHED
        self.timer.finished_at = timezone.now()
        self.timer.save()

        # Criar evento
        TimerEvent.objects.create(
            timer=self.timer,
            event_type='finished'
        )

        # Chain of Responsibility: propagar efeitos para cronômetro pai
        from .timer_chain import TimerEventChain
        chain = TimerEventChain()
        chain.handle_timer_finished(self.timer)

        return {"success": True, "message": "Cronômetro finalizado"}