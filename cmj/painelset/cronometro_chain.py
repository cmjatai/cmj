
from abc import ABC, abstractmethod
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
        if cronometro.parent and cronometro.pause_parent_on_start:
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
                "type": "cronometro_update",
                "cronometro_id": str(cronometro.id),
                "state": cronometro.state,
                "elapsed_time": cronometro.elapsed_time.total_seconds(),
                "remaining_time": cronometro.remaining_time.total_seconds(),
            }
        )

        # Se tem pai, notificar também sobre mudanças na hierarquia
        if cronometro.parent:
            async_to_sync(channel_layer.group_send)(
                f"cronometro_{cronometro.parent.id}",
                {
                    "type": "child_cronometro_update",
                    "child_cronometro_id": str(cronometro.id),
                    "parent_cronometro_id": str(cronometro.parent.id),
                    "state": cronometro.state,
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
        notification = NotificationHandler()

        # Configura a ordem da cadeia
        pause_parent.set_next(notification)

        return pause_parent

    def handle_cronometro_finished(self, cronometro):
        """Processa eventos quando um cronômetro termina"""
        return self.chain.handle(cronometro, {"event": "finished"})

    def handle_cronometro_stopped(self, cronometro):
        """Processa eventos quando um cronômetro é parado"""
        return self.chain.handle(cronometro, {"event": "stopped"})