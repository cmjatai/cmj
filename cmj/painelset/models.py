
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.translation import gettext_lazy as _

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.json import JSONField

from sapl.utils import SaplGenericForeignKey

class CronometroState(models.TextChoices):
    """Estados possíveis de um cronômetro"""
    STOPPED = 'stopped', 'Parado'
    RUNNING = 'running', 'Executando'
    PAUSED = 'paused', 'Pausado'
    FINISHED = 'finished', 'Finalizado'

class CronometroMixin:

    def get_or_create_unique_cronometro(self, duration=None):
        """Obtém ou cria um cronômetro único associado ao modelo que o chamou este método."""
        duration_owner = getattr(self, 'duration', timedelta())
        try:
            cronometro, created = Cronometro.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.id,
                defaults={
                    'name': f'Cronômetro do {self._meta.verbose_name}: {self.name}',
                    'duration': duration,
                }
            )
        except:
            cronometro, created = Cronometro.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.id,
                name = f'Cronômetro do {self._meta.verbose_name}: {self.name}',
                duration = duration_owner
            )
        if not created and hasattr(self, 'duration') and cronometro.duration != duration_owner:
            cronometro.duration = duration or duration_owner
            cronometro.save()

        return cronometro, created


class Cronometro(models.Model):
    """
    Modelo principal do cronômetro usando padrão Composite
    Pode ter cronômetros filhos e um cronômetro pai
    """
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1024)

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
    def last_paused_time(self):
        """Calcula o tempo desde a última pausa"""
        if self.state == CronometroState.PAUSED and self.paused_at:
            return timezone.now() - self.paused_at
        return timedelta()

    @property
    def elapsed_time(self):
        """Calcula tempo decorrido"""
        if self.state == CronometroState.STOPPED:
            return timedelta()

        if self.state == CronometroState.RUNNING and self.started_at:
            tn = timezone.now()
            r = self.accumulated_time + (tn - self.started_at)
            return r

        return self.accumulated_time

    @property
    def remaining_time(self):
        """Calcula tempo restante"""
        elapsed = self.elapsed_time
        #return max(timedelta(), self.duration - elapsed)
        return self.duration - elapsed

    @property
    def started_time(self):
        """Retorna o timestamp de início"""
        return self.started_at.timestamp() if self.started_at else None
    @property
    def paused_time(self):
        """Retorna o timestamp de pausa"""
        return self.paused_at.timestamp() if self.paused_at else None

    def ws_serialize(self):
        from cmj.api.serializers_painelset import CronometroSerializer
        return CronometroSerializer(self).data

class CronometroEvent(models.Model):
    """Modelo para registrar eventos de cronômetros - Observer Pattern"""
    EVENT_TYPES = [
        ('started', 'Iniciado'),
        ('paused', 'Pausado'),
        ('resumed', 'Retomado'),
        ('stopped', 'Parado'),
        ('finished', 'Finalizado'),
        ('reset', 'Resetado'),
        ('time_added', 'Tempo Adicionado'),
    ]

    cronometro = models.ForeignKey(Cronometro, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    triggered_by_child = models.ForeignKey(Cronometro, on_delete=models.SET_NULL,
                                          null=True, blank=True,
                                          related_name='triggered_events',
                                          help_text="Cronômetro filho que causou este evento")

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    class Meta:
        verbose_name = "Evento de Cronômetro"
        verbose_name_plural = "Eventos de Cronômetros"
        ordering = ['-timestamp']



class Evento(models.Model, CronometroMixin):
    """Modelo para representar um Evento que é a representação de uma reunião que possui tempo global, partes menores e pontos que representam indivíduos."""
    name = models.CharField(max_length=256, verbose_name="Nome do Evento")
    description = models.TextField(blank=True, verbose_name="Descrição do Evento")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    start_previsto = models.DateTimeField(null=True, blank=True, verbose_name="Data e hora Prevista de Início")

    start_real = models.DateTimeField(null=True, blank=True, verbose_name="Data e hora Real de Início")
    end_real = models.DateTimeField(null=True, blank=True, verbose_name="Data e hora Real de Término")

    duration = models.DurationField(help_text="Duração total planejada do evento", verbose_name="Duração do Evento")

    ips_mesas = models.CharField(
        max_length=256, blank=True, default='',
        help_text="IPs das mesas associadas a este indivíduo, separados por vírgula",
       validators=[
           RegexValidator(
               regex=r'^(\d{1,3}(\.\d{1,3}){3})*(\s(\d{1,3}(\.\d{1,3}){3}))*$',
               message="IP inválido. Formato esperado: xxx.xxx.xxx.xxx (separados por espaço para múltiplos IPs).",
               code='invalid_ip'
           )
       ]
    )
    comunicar_com_mesas = models.BooleanField(default=False, verbose_name="Comunicar com Mesas", help_text="Comunicar com mesas via OSC?")

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

class RoleChoices(models.TextChoices):
    PARLAMENTAR = 'PARLAMENTAR', 'Parlamentar'
    TRIBUNA = 'TRIBUNA', 'Tribuna'
    INDIVIDUO = 'INDIVIDUO', 'Indivíduo'

class IndividuoManager(models.Manager):

    def reset_ordem(self):
        individuos = self.get_queryset()
        individuos = sorted(list(individuos), key=lambda x: (RoleChoices.names.index(x.role), x.name))

        for sr, i in enumerate(individuos, 1):
            i.order = sr
            i.save()

    def reposicione(self, pk, idx):
        individuo = self.get_queryset().filter(pk=pk).first()
        if not individuo:
            return
        evento = individuo.evento
        if not evento:
            return
        individuos = list(evento.individuos.all().order_by('order'))
        if individuo not in individuos:
            return

        individuos.remove(individuo)
        individuos.insert(idx-1, individuo)

        for sr, i in enumerate(individuos, 1):
            if i.order != sr:
                i.order = sr
                i.save()
        return individuo


class Individuo(models.Model, CronometroMixin):
    objects = IndividuoManager()

    """Modelo para representar um Individuo no Painel SET, que representa um indivíduo ou tópico."""
    name = models.CharField(max_length=1024)
    role = models.CharField(
        max_length=100, blank=True, help_text="Função ou papel do indivíduo",
        choices=RoleChoices.choices
    )
    order = models.PositiveIntegerField(help_text="Ordem do indivíduo no Evento", default=0)

    canal = models.PositiveIntegerField(help_text="Canal do indivíduo no Evento", default=0)

    ips_mesas = models.CharField(
        max_length=256, blank=True, default='',
        help_text="IPs das mesas associadas a este indivíduo, separados por vírgula",
       validators=[
           RegexValidator(
               regex=r'^(\d{1,3}(\.\d{1,3}){3})*(\s(\d{1,3}(\.\d{1,3}){3}))*$',
               message="IP inválido. Formato esperado: xxx.xxx.xxx.xxx (separados por espaço para múltiplos IPs).",
               code='invalid_ip'
           )
       ]
    )

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

    status_microfone = models.BooleanField(default=False, help_text="Indica se o microfone está ativo para este indivíduo")
    microfone_sempre_ativo = models.BooleanField(default=False, help_text="Indica se o microfone deste indivíduo deve estar sempre ativo")
    tempo_de_corte_microfone = models.DurationField(default=timedelta(seconds=5), help_text="Duração do corte de microfone após o tempo do cronômetro zerar")

    com_a_palavra = models.BooleanField(default=False, help_text="Indica se o indivíduo está com a palavra")

    aparteante = models.OneToOneField(
        'self',
        blank=True, null=True, default=None,
        related_name='aparteado',
        on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ['order']
    unique_together = [
        ('evento', 'parlamentar', 'role', 'name',)
    ]

    def __str__(self):
        return f"{self.name} ({self.role})"

    def ws_serialize(self):
        from cmj.api.serializers_painelset import IndividuoSerializer
        return IndividuoSerializer(self).data

    @property
    def channel_display(self):
        if self.canal == 0:
            return f'{self.order:>02}'
        return f'{self.canal:>02}'

    @property
    def ips(self):
        """Retorna a lista de IPs associados ao indivíduo"""
        ips = self.ips_mesas
        if not ips.strip():
            ips = self.evento.ips_mesas
        if not ips.strip():
            return []
        return [ip.strip() for ip in ips.split() if ip.strip()]