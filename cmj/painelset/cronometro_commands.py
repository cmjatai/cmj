
from abc import ABC, abstractmethod
from django.utils import timezone
from datetime import timedelta
from .models import Cronometro, CronometroState, CronometroEvent

class CronometroCommand(ABC):
    """
    Command Pattern: Interface base para comandos de cronômetro
    """

    def __init__(self, cronometro_id):
        self.cronometro_id = cronometro_id
        self.cronometro = None

    def execute(self):
        """Executa o comando"""
        try:
            self.cronometro = Cronometro.objects.get(id=self.cronometro_id)
            return self._execute_command()
        except Cronometro.DoesNotExist:
            return {"error": "Cronômetro não encontrado"}

    @abstractmethod
    def _execute_command(self):
        """Implementação específica do comando"""
        pass

class StartCronometroCommand(CronometroCommand):
    """Comando para iniciar cronômetro"""

    def _execute_command(self):
        if self.cronometro.state != CronometroState.STOPPED:
            return {"error": "Cronômetro já está em execução ou pausado"}

        self.cronometro.state = CronometroState.RUNNING
        self.cronometro.started_at = timezone.now()
        self.cronometro.accumulated_time = timedelta()
        self.cronometro.save()

        # Criar evento
        CronometroEvent.objects.create(
            cronometro=self.cronometro,
            event_type='started'
        )

        return {"success": True, "message": "Cronômetro iniciado"}

class PauseCronometroCommand(CronometroCommand):
    """Comando para pausar cronômetro"""

    def _execute_command(self):
        if self.cronometro.state != CronometroState.RUNNING:
            return {"error": "Cronômetro não está em execução"}

        # Acumular tempo decorrido
        if self.cronometro.started_at:
            elapsed = timezone.now() - self.cronometro.started_at
            self.cronometro.accumulated_time += elapsed

        self.cronometro.state = CronometroState.PAUSED
        self.cronometro.paused_at = timezone.now()
        self.cronometro.save()

        # Criar evento
        CronometroEvent.objects.create(
            cronometro=self.cronometro,
            event_type='paused'
        )

        return {"success": True, "message": "Cronômetro pausado"}

class ResumeCronometroCommand(CronometroCommand):
    """Comando para retomar cronômetro pausado"""

    def _execute_command(self):
        if self.cronometro.state != CronometroState.PAUSED:
            return {"error": "Cronômetro não está pausado"}

        self.cronometro.state = CronometroState.RUNNING
        self.cronometro.started_at = timezone.now()
        self.cronometro.paused_at = None
        self.cronometro.save()

        # Criar evento
        CronometroEvent.objects.create(
            cronometro=self.cronometro,
            event_type='resumed'
        )

        return {"success": True, "message": "Cronômetro retomado"}

class StopCronometroCommand(CronometroCommand):
    """Comando para parar cronômetro"""

    def _execute_command(self):
        if self.cronometro.state == CronometroState.STOPPED:
            return {"error": "Cronômetro já está parado"}

        # Parar cronômetros filhos primeiro
        for child in self.cronometro.get_children():
            if child.state in [CronometroState.RUNNING, CronometroState.PAUSED]:
                StopCronometroCommand(child.id).execute()

        self.cronometro.state = CronometroState.STOPPED
        self.cronometro.started_at = None
        self.cronometro.paused_at = None
        self.cronometro.accumulated_time = timedelta()
        self.cronometro.save()

        # Criar evento
        CronometroEvent.objects.create(
            cronometro=self.cronometro,
            event_type='stopped'
        )

        return {"success": True, "message": "Cronômetro parado"}

class FinishCronometroCommand(CronometroCommand):
    """Comando para finalizar cronômetro (quando tempo acaba)"""

    def _execute_command(self):
        if self.cronometro.state != CronometroState.RUNNING:
            return {"error": "Cronômetro não está em execução"}

        self.cronometro.state = CronometroState.FINISHED
        self.cronometro.finished_at = timezone.now()
        self.cronometro.save()

        # Criar evento
        CronometroEvent.objects.create(
            cronometro=self.cronometro,
            event_type='finished'
        )

        # Chain of Responsibility: propagar efeitos para cronômetro pai
        from .cronometro_chain import CronometroEventChain
        chain = CronometroEventChain()
        chain.handle_cronometro_finished(self.cronometro)

        return {"success": True, "message": "Cronômetro finalizado"}