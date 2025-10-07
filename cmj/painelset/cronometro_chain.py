
from abc import ABC, abstractmethod

from cmj.api.serializers_painelset import CronometroTreeSerializer
from .models import Cronometro, CronometroState, CronometroEvent

class CronometroEventHandler(ABC):
    """
    Chain of Responsibility Pattern: Handler base para eventos de cronômetro
    """

    def __init__(self):
        self._next_handler = None

    def set_next(self, handler):
        """Define o próximo handler na cadeia"""
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, cronometro, event_data=None):
        """Tenta processar o evento ou passa para o próximo handler"""
        if self._next_handler:
            return self._next_handler.handle(cronometro, event_data)
        return None

class PauseParentHandler(CronometroEventHandler):
    """Handler para pausar cronômetro pai quando filho iniciar"""

    def handle(self, cronometro, event_data=None):
        if cronometro.parent and \
            cronometro.pause_parent_on_start and \
            event_data and event_data.get('event') == 'started':
            # Importação local para evitar circular import
            from .cronometro_commands import PauseCronometroCommand

            result = PauseCronometroCommand(cronometro.parent.id).execute()

            # Registrar que foi causado pelo filho
            if result.get('success'):
                CronometroEvent.objects.create(
                    cronometro=cronometro.parent,
                    event_type='paused',
                    triggered_by_child=cronometro
                )
        return super().handle(cronometro, event_data)

class ResumeHandler(CronometroEventHandler):

    def handle(self, cronometro, event_data=None):
        if event_data and event_data.get('event') == 'resumed':
            if cronometro and cronometro.state == CronometroState.PAUSED:
                from .cronometro_commands import ResumeCronometroCommand

                result = ResumeCronometroCommand(cronometro).execute()

                if result.get('success'):
                    CronometroEvent.objects.create(
                        cronometro=cronometro,
                        event_type='resumed',
                        triggered_by_child=None
                    )

        # Continuar cadeia
        return super().handle(cronometro, event_data)

class NotificationHandler(CronometroEventHandler):
    """Handler para enviar notificações via WebSocket"""

    def handle(self, cronometro, event_data=None):
        # Importação local para evitar circular import
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()

        # Notificar sobre mudança no cronômetro
        async_to_sync(channel_layer.group_send)(
            f"cronometro_{cronometro.id}",
            {
                "type": "command_result",
                "command": 'get',
                "result": {
                    'cronometro': CronometroTreeSerializer(cronometro).data
                }
            }
        )

        # Se tem pai, notificar também sobre mudanças na hierarquia
        if cronometro.parent:
            async_to_sync(channel_layer.group_send)(
                f"cronometro_{cronometro.parent.id}",
                {
                    "type": "command_result",
                    "command": 'get',
                    "result": {
                        'cronometro':CronometroTreeSerializer(cronometro.parent).data
                    }
                }
            )

        # Continuar cadeia
        return super().handle(cronometro, event_data)

class CronometroEventChain:
    """
    Classe para configurar e usar a cadeia de responsabilidade
    """

    def __init__(self):
        self.chain = self._build_chain()

    def _build_chain(self):
        """Constrói a cadeia de handlers"""
        pause_parent = PauseParentHandler()
        resume = ResumeHandler()
        notification = NotificationHandler()

        # Configura a ordem da cadeia
        pause_parent.set_next(resume)
        resume.set_next(notification)

        return pause_parent

    def handle_cronometro_finished(self, cronometro):
        """Processa eventos quando um cronômetro termina"""
        return self.chain.handle(cronometro, {"event": "finished"})

    def handle_cronometro_resumed(self, cronometro):
        """Processa eventos quando um cronômetro é retomado"""
        return self.chain.handle(cronometro, {"event": "resumed"})

    def handle_cronometro_started(self, cronometro):
        """Processa eventos quando um cronômetro é iniciado"""
        return self.chain.handle(cronometro, {"event": "started"})

    def handle_cronometro_stopped(self, cronometro):
        """Processa eventos quando um cronômetro é parado"""
        return self.chain.handle(cronometro, {"event": "stopped"})