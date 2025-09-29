from django.db import models
from django.utils import timezone
from datetime import timedelta
from enum import Enum
import uuid

class TimerState(models.TextChoices):
    """Estados possíveis de um cronômetro"""
    STOPPED = 'stopped', 'Parado'
    RUNNING = 'running', 'Executando'
    PAUSED = 'paused', 'Pausado'
    FINISHED = 'finished', 'Finalizado'

class Timer(models.Model):
    """
    Modelo principal do cronômetro usando padrão Composite
    Pode ter cronômetros filhos e um cronômetro pai
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    # Composite Pattern: self-referencing para hierarquia
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                              null=True, blank=True, related_name='children')

    # Configurações do cronômetro
    duration = models.DurationField(help_text="Duração planejada do cronômetro")

    # State Pattern: estado atual
    state = models.CharField(choices=TimerState.choices,
                           default=TimerState.STOPPED, max_length=20)

    # Timestamps para controle
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Configuração de comportamento hierárquico
    stop_parent_on_finish = models.BooleanField(default=False,
        help_text="Se True, para o cronômetro pai quando este terminar")
    reduce_parent_time = models.BooleanField(default=False,
        help_text="Se True, reduz simultaneamente o tempo do cronômetro pai")

    # Tempo acumulado (para pausas)
    accumulated_time = models.DurationField(default=timedelta())

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} ({self.state})"

    # Composite Pattern: métodos para gerenciar hierarquia
    def get_children(self):
        """Retorna cronômetros filhos"""
        return self.children.all()

    def get_descendants(self):
        """Retorna todos os descendentes (filhos, netos, etc.)"""
        descendants = []
        for child in self.get_children():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def get_root(self):
        """Retorna o cronômetro raiz da hierarquia"""
        if self.parent is None:
            return self
        return self.parent.get_root()

    def is_leaf(self):
        """Verifica se é um cronômetro folha (sem filhos)"""
        return not self.children.exists()

    @property
    def elapsed_time(self):
        """Calcula tempo decorrido"""
        if self.state == TimerState.STOPPED:
            return timedelta()

        if self.state == TimerState.RUNNING and self.started_at:
            return self.accumulated_time + (timezone.now() - self.started_at)

        return self.accumulated_time

    @property
    def remaining_time(self):
        """Calcula tempo restante"""
        elapsed = self.elapsed_time
        return max(timedelta(), self.duration - elapsed)

class TimerEvent(models.Model):
    """Modelo para registrar eventos de cronômetros - Observer Pattern"""
    EVENT_TYPES = [
        ('started', 'Iniciado'),
        ('paused', 'Pausado'),
        ('resumed', 'Retomado'),
        ('stopped', 'Parado'),
        ('finished', 'Finalizado'),
        ('reset', 'Resetado'),
    ]

    timer = models.ForeignKey(Timer, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    triggered_by_child = models.ForeignKey(Timer, on_delete=models.SET_NULL,
                                          null=True, blank=True,
                                          related_name='triggered_events',
                                          help_text="Cronômetro filho que causou este evento")

    class Meta:
        ordering = ['-timestamp']