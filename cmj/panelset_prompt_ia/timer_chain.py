
from abc import ABC, abstractmethod
from .models import Timer, TimerState, TimerEvent

class TimerEventHandler(ABC):
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
    def handle(self, timer, event_data=None):
        """Tenta processar o evento ou passa para o próximo handler"""
        if self._next_handler:
            return self._next_handler.handle(timer, event_data)
        return None

class StopParentHandler(TimerEventHandler):
    """Handler para parar cronômetro pai quando filho terminar"""

    def handle(self, timer, event_data=None):
        if timer.parent and timer.stop_parent_on_finish:
            # Importação local para evitar circular import
            from .timer_commands import StopTimerCommand

            result = StopTimerCommand(timer.parent.id).execute()

            # Registrar que foi causado pelo filho
            if result.get('success'):
                TimerEvent.objects.create(
                    timer=timer.parent,
                    event_type='stopped',
                    triggered_by_child=timer
                )

        # Continuar cadeia
        return super().handle(timer, event_data)

class ReduceParentTimeHandler(TimerEventHandler):
    """Handler para reduzir tempo do cronômetro pai proporcionalmente"""

    def handle(self, timer, event_data=None):
        if timer.parent and timer.reduce_parent_time:
            parent = timer.parent
            if parent.state == TimerState.RUNNING:
                # Reduzir tempo do pai baseado no tempo decorrido do filho
                elapsed_ratio = timer.elapsed_time / timer.duration
                time_to_reduce = parent.duration * elapsed_ratio * 0.1  # 10% do tempo proporcional

                parent.accumulated_time += time_to_reduce
                parent.save()

        # Continuar cadeia
        return super().handle(timer, event_data)

class NotificationHandler(TimerEventHandler):
    """Handler para enviar notificações via WebSocket"""

    def handle(self, timer, event_data=None):
        # Importação local para evitar circular import
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()

        # Notificar sobre mudança no cronômetro
        async_to_sync(channel_layer.group_send)(
            f"timer_{timer.id}",
            {
                "type": "timer_update",
                "timer_id": str(timer.id),
                "state": timer.state,
                "elapsed_time": timer.elapsed_time.total_seconds(),
                "remaining_time": timer.remaining_time.total_seconds(),
            }
        )

        # Se tem pai, notificar também sobre mudanças na hierarquia
        if timer.parent:
            async_to_sync(channel_layer.group_send)(
                f"timer_{timer.parent.id}",
                {
                    "type": "child_timer_update",
                    "child_timer_id": str(timer.id),
                    "parent_timer_id": str(timer.parent.id),
                    "state": timer.state,
                }
            )

        # Continuar cadeia
        return super().handle(timer, event_data)

class TimerEventChain:
    """
    Classe para configurar e usar a cadeia de responsabilidade
    """

    def __init__(self):
        self.chain = self._build_chain()

    def _build_chain(self):
        """Constrói a cadeia de handlers"""
        stop_parent = StopParentHandler()
        reduce_parent = ReduceParentTimeHandler()
        notification = NotificationHandler()

        # Configura a ordem da cadeia
        stop_parent.set_next(reduce_parent).set_next(notification)

        return stop_parent

    def handle_timer_finished(self, timer):
        """Processa eventos quando um cronômetro termina"""
        return self.chain.handle(timer, {"event": "finished"})

    def handle_timer_stopped(self, timer):
        """Processa eventos quando um cronômetro é parado"""
        return self.chain.handle(timer, {"event": "stopped"})