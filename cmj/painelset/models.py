from enum import unique
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation

from sapl.utils import SaplGenericForeignKey

class CronometroState(models.TextChoices):
    """Estados possíveis de um cronômetro"""
    STOPPED = 'stopped', 'Parado'
    RUNNING = 'running', 'Executando'
    PAUSED = 'paused', 'Pausado'
    FINISHED = 'finished', 'Finalizado'

class Cronometro(models.Model):
    """
    Modelo principal do cronômetro usando padrão Composite
    Pode ter cronômetros filhos e um cronômetro pai
    """
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    # Composite Pattern: self-referencing para hierarquia
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                              null=True, blank=True, related_name='children')

    # Configurações do cronômetro
    duration = models.DurationField(help_text="Duração planejada do cronômetro")

    # State Pattern: estado atual
    state = models.CharField(choices=CronometroState.choices,
                           default=CronometroState.STOPPED, max_length=20)

    # Timestamps para controle
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Configuração de comportamento hierárquico
    pause_parent_on_start = models.BooleanField(default=False,
        help_text="Pausar o cronômetro pai quando este iniciar")

    # Tempo acumulado (para pausas)
    accumulated_time = models.DurationField(default=timedelta())

    content_type = models.ForeignKey(ContentType, blank=True, null=True, default=None, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField(blank=True, null=True, default=None)
    vinculo = SaplGenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "Cronômetro"
        verbose_name_plural = "Cronômetros"
        ordering = ['created_at']
        unique_together = [
            ('content_type', 'object_id',)
        ]

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
        if self.state == CronometroState.STOPPED:
            return timedelta()

        if self.state == CronometroState.RUNNING and self.started_at:
            return self.accumulated_time + (timezone.now() - self.started_at)

        return self.accumulated_time

    @property
    def remaining_time(self):
        """Calcula tempo restante"""
        elapsed = self.elapsed_time
        return max(timedelta(), self.duration - elapsed)

class CronometroEvent(models.Model):
    """Modelo para registrar eventos de cronômetros - Observer Pattern"""
    EVENT_TYPES = [
        ('started', 'Iniciado'),
        ('paused', 'Pausado'),
        ('resumed', 'Retomado'),
        ('stopped', 'Parado'),
        ('finished', 'Finalizado'),
        ('reset', 'Resetado'),
    ]

    cronometro = models.ForeignKey(Cronometro, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    triggered_by_child = models.ForeignKey(Cronometro, on_delete=models.SET_NULL,
                                          null=True, blank=True,
                                          related_name='triggered_events',
                                          help_text="Cronômetro filho que causou este evento")

    class Meta:
        verbose_name = "Evento de Cronômetro"
        verbose_name_plural = "Eventos de Cronômetros"
        ordering = ['-timestamp']


class Evento(models.Model):
    """Modelo para representar um Evento que é a representação de uma reunião que possui tempo global, partes menores e pontos que representam indivíduos."""
    name = models.CharField(max_length=100, verbose_name="Nome do Evento", unique=True)
    description = models.TextField(blank=True, verbose_name="Descrição do Evento")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    start_previsto = models.DateTimeField(null=True, blank=True, verbose_name="Data e hora Prevista de Início")
    
    start_real = models.DateTimeField(null=True, blank=True, verbose_name="Data e hora Real de Início")
    end_real = models.DateTimeField(null=True, blank=True, verbose_name="Data e hora Real de Término")

    duration = models.DurationField(help_text="Duração total planejada do evento", verbose_name="Duração do Evento")

    cronometro = GenericRelation(
        Cronometro,
        related_query_name='eventos',
        verbose_name="Cronômetro do Evento",
        help_text="Cronômetro associado ao Evento")

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class ParteEvento(models.Model):
    """Modelo para representar uma Parte de um Evento, que possui um tempo específico."""
    name = models.CharField(max_length=100)
    duration = models.DurationField(help_text="Duração planejada da parte")
    order = models.PositiveIntegerField(help_text="Ordem da parte no Evento", default=0)

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE,
                                   related_name='parts', help_text="Evento ao qual esta parte pertence")

    cronometro = GenericRelation(
        Cronometro,
        related_query_name='eventos',
        verbose_name="Cronômetro da Parte do Evento",
        help_text="Cronômetro associado à Parte do Evento")

    class Meta:

        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.duration})"

class RoleChoices(models.TextChoices):
    PARLAMENTAR = 'PARLAMENTAR', 'Parlamentar'
    TRIBUNA = 'TRIBUNA', 'Tribuna'
    INDIVIDUO = 'INDIVIDUO', 'Indivíduo'

class IndividuoManager(models.Manager):

    def reordene(self, exclude_pk=None):
        individuos = self.get_queryset()
        if exclude_pk:
            individuos = list(individuos.exclude(pk=exclude_pk))

        for sr, i in enumerate(individuos, 1):
            i.order = sr
            i.save()

    def reset_ordem(self):
        individuos = self.get_queryset()
        individuos = sorted(list(individuos), key=lambda x: (RoleChoices.names.index(x.role), x.name))

        for sr, i in enumerate(individuos, 1):
            i.order = sr
            i.save()

    def reposicione(self, pk, idx):
        individuos = self.reordene(exclude_pk=pk)

        self.get_queryset(
        ).filter(
            order__gte=idx
        ).update(
            order=models.F('order') + 1
        )

        self.get_queryset(
        ).filter(
            pk=pk
        ).update(
            order=idx
        )


class Individuo(models.Model):
    objects = IndividuoManager()

    """Modelo para representar um Individuo no Painel SET, que representa um indivíduo ou tópico."""
    name = models.CharField(max_length=100)
    role = models.CharField(
        max_length=100, blank=True, help_text="Função ou papel do indivíduo",
        choices=RoleChoices.choices
    )
    order = models.PositiveIntegerField(help_text="Ordem do indivíduo no Evento", default=0)

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, verbose_name="Evento",
                                   related_name='individuos', help_text="Evento ao qual este indivíduo pertence")

    parlamentar = models.ForeignKey('parlamentares.Parlamentar', on_delete=models.CASCADE,
                                    null=True, blank=True, verbose_name="Parlamentar",
                                   related_name='individuos', help_text="Parlamentar associado ao indivíduo")

    cronometro = GenericRelation(
        Cronometro,
        related_query_name='individuos',
        verbose_name="Cronômetro do Individuo",
        help_text="Cronômetro associado ao Individuo")

    class Meta:
        ordering = ['order']
    unique_together = [
        ('evento', 'parlamentar', 'role', 'name',)
    ]

    def __str__(self):
        return f"{self.name} ({self.role})"