
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.translation import gettext_lazy as _

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.json import JSONField
import yaml

from sapl.base.templatetags.common_tags import youtube_id
from sapl.parlamentares.models import foto_upload_path
from sapl.utils import SaplGenericForeignKey
from sapl.utils import PortalImageCropField
from image_cropping.fields import ImageRatioField


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

    youtube_id = models.CharField(
        max_length=256, blank=True, default='',
        help_text="ID do vídeo do YouTube associado ao evento (para exibição no painel)",
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_-]{11}$',
                message="ID do YouTube inválido. Deve conter 11 caracteres alfanuméricos, hífens ou underscores.",
                code='invalid_youtube_id'
            )
        ]
    )

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

    def reset_to_defaults(self):
        """Reseta os paineis do evento para a configuração padrão, removendo visões e widgets atuais."""

        fixture_file = settings.BASE_DIR.child('painelset', 'fixtures', 'painelset_defaults.yaml')

        self.paineis.all().delete()

        painelset_set = {}
        try:
            with open(fixture_file, 'r') as file:
                painelset_set = yaml.safe_load(file)
        except Exception as e:
            print(f"Erro ao carregar fixture de paineis padrão: {e}")
            return

        painelset_set = painelset_set.get('paineis', [])

        for painel_data in painelset_set:

            if not painel_data.get('painel', None):
                continue

            painel = Painel()
            painel.evento = self
            painel.name = painel_data['name']
            painel.description = painel_data['description']
            painel.principal = painel_data.get('principal', False)
            painel.config = painel_data.get('config', {})
            painel.styles = painel_data.get('styles', {})
            painel.save()

            for visao_data in painel_data.get('visoes', []):
                visao = VisaoDePainel.objects.create(
                    painel=painel,
                    name=visao_data['name'],
                    active=False,
                    description=visao_data['description'],
                    config=visao_data.get('config', {}),
                    styles=visao_data.get('styles', {})
                )
                painel.visoes.add(visao)

                for widget_data in visao_data.get('widgets', []):
                    widget = Widget.objects.create(
                        visao=visao,
                        name=widget_data['name'],
                        description=widget_data['description'],
                        vue_component=widget_data.get('vue_component', ''),
                        config=widget_data.get('config', {}),
                        styles=widget_data.get('styles', {})
                    )
                    visao.widgets.add(widget)
            visao.active = True
            visao.save()

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
    auto_corte_microfone = models.BooleanField(default=False, help_text="Indica se o microfone foi cortado automaticamente")

    microfone_sempre_ativo = models.BooleanField(default=False, help_text="Indica se o microfone deste indivíduo deve estar sempre ativo")
    tempo_de_corte_microfone = models.DurationField(default=timedelta(seconds=5), help_text="Duração do corte de microfone após o tempo do cronômetro zerar")

    com_a_palavra = models.BooleanField(default=False, help_text="Indica se o indivíduo está com a palavra")

    aparteante = models.OneToOneField(
        'self',
        blank=True, null=True, default=None,
        related_name='aparteado',
        on_delete=models.SET_NULL
    )

    fotografia = PortalImageCropField(
        verbose_name=_('Fotografia'), upload_to=foto_upload_path, null=True, blank=True)  # validators=[restringe_tipos_de_arquivo_img],
    fotografia_cropping = ImageRatioField(
        'fotografia', '128x128', verbose_name=_('Avatar'), size_warning=True,
        help_text=_('A configuração do Avatar '
                    'é possível após a atualização da fotografia.'))

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.role})"

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.order == 0:
            max_order = Individuo.objects.filter(evento=self.evento).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1

        if not self.pk:
            fotografia = None
            if self.fotografia:
                fotografia = self.fotografia
                self.fotografia = None

            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)

            self.fotografia = fotografia

        return models.Model.save(self, force_insert=False,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)

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

class Painel(models.Model):
    """Modelo para representar um painel que pode exibir visões."""
    name = models.CharField(max_length=256, help_text="Nome único do painel")
    description = models.TextField(blank=True, help_text="Descrição do painel")

    principal = models.BooleanField(default=False, help_text="Indica se este painel é o principal")
    auto_select_visoes = models.BooleanField(default=True, help_text="Selecionar automaticamente visões com base no contexto do evento")

    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, verbose_name="Evento",
        blank=True, null=True, related_name='paineis', help_text="Evento ao qual este painel pertence")

    sessao = models.ForeignKey(
        'sessao.SessaoPlenaria', on_delete=models.SET_NULL, verbose_name="Sessão Plenária Associada",
        blank=True, null=True, related_name='paineis', help_text="Sessão ao qual este painel pertence")

    config = JSONField(
        verbose_name=_('Configuração Específica'),
        help_text="Configuração específica da visão neste painel em formato JSON",
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)
    styles = JSONField(
        verbose_name=_('Estilos Específicos'),
        help_text="Estilos específicos da visão neste painel em formato JSON",
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)

    class Meta:
        verbose_name = "Painel"
        verbose_name_plural = "Painéis"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def visao_ativa(self):
        """Retorna a visão ativa do painel, se houver."""
        visao_ativa = self.visoes.filter(active=True).values_list(flat=True).first()
        if visao_ativa:
            return visao_ativa
        return None

    def ws_serialize(self):
        from drfautoapi.drfautoapi import ApiViewSetConstrutor
        PainelSerializer = ApiViewSetConstrutor._built_sets[
            self._meta.app_config][self._meta.model].serializer_class
        return PainelSerializer(self).data

    def copy(self, evento=None, sessao=None):
        """Copia deste painel para novo evento e sessão, ou nenhum deles, incluindo suas visões e widgets."""
        novo_painel = Painel.objects.create(
            name=f"{self.name}",
            description=self.description,
            principal=self.principal,
            evento=evento,
            sessao=sessao,
            config=self.config,
            styles=self.styles
        )
        for visao in self.visoes.all():
            nova_visao = VisaoDePainel.objects.create(
                name=visao.name,
                description=visao.description,
                painel=novo_painel,
                position=visao.position,
                active=visao.active,
                config=visao.config,
                styles=visao.styles
            )

            map_widgets = {}
            for widget in visao.widgets.all():
                widget_copiado = widget.id
                widget.pk = None
                widget.visao = nova_visao
                widget.save()
                map_widgets[widget_copiado] = widget.id

            for widget in nova_visao.widgets.all():
                if widget.parent_id in map_widgets:
                    widget.parent_id = map_widgets[widget.parent_id]
                    widget.save()


class VisaoDePainel(models.Model):
    """Modelo intermediário para associar visões a painéis com configuração adicional."""

    name = models.CharField(max_length=256, blank=True, help_text="Nome da Visão no Painel Associado")
    description = models.TextField(blank=True, help_text="Descrição da visão no Painel Associado")

    painel = models.ForeignKey(Painel, on_delete=models.CASCADE, help_text="Painel associado", related_name="visoes")

    position = models.PositiveIntegerField(help_text="Posição da visão no painel", default=0)

    active = models.BooleanField(default=False, help_text="Indica se a visão está ativa no painel")

    config = JSONField(
        verbose_name=_('Configuração Específica'),
        help_text="Configuração específica da visão neste painel em formato JSON",
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)
    styles = JSONField(
        verbose_name=_('Estilos Específicos'),
        help_text="Estilos específicos da visão neste painel em formato JSON",
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)

    class Meta:
        verbose_name = "Visão do Painel"
        verbose_name_plural = "Visões dos Painéis"
        ordering = ['position']

    def __str__(self):
        return f"{self.name} no painel {self.painel.name}"

    def activate(self):
        """Ativa esta visão no painel, desativando as outras."""
        for vp in VisaoDePainel.objects.filter(painel=self.painel):
            if vp.active and vp != self:
                vp.active = False
                vp.save()
        self.active = True
        self.save()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.position == 0:
            max_position = VisaoDePainel.objects.filter(painel=self.painel).aggregate(models.Max('position'))['position__max']
            self.position = (max_position or 0) + 1

        return super().save(force_insert=force_insert,
                            force_update=force_update,
                            using=using,
                            update_fields=update_fields)

class Widget(models.Model):
    """Modelo intermediário para associar widgets a visões com configuração adicional."""

    name = models.CharField(max_length=256, blank=True, help_text="Nome do Widget na Visão Associada")
    description = models.TextField(blank=True, help_text="Descrição do Widget na Visão Associada")

    visao = models.ForeignKey(VisaoDePainel, on_delete=models.CASCADE, help_text="Visão associada", related_name="widgets")

    position = models.PositiveIntegerField(help_text="Posição do widget na visão", default=0)
    visible = models.BooleanField(default=True, help_text="Indica se o widget está visível na visão")

    config = JSONField(
        verbose_name=_('Configuração Específica'),
        help_text="Configuração específica do widget nesta visão em formato JSON",
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)

    styles = JSONField(
        verbose_name=_('Estilos Específicos'),
        help_text="Estilos específicos do widget nesta visão em formato JSON",
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)

    vue_component = models.CharField(
        max_length=256, help_text="Nome do componente Vue.js associado ao widget",
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z][A-Za-z0-9_]*$',
                message="Nome do componente inválido. Deve começar com uma letra maiúscula e conter apenas letras, números e underscores.",
                code='invalid_component_name'
            )
        ]
    )

    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                              null=True, blank=True, related_name='children',
                              help_text="Widget pai para hierarquia")

    class Meta:
        verbose_name = "Widget da Visão"
        verbose_name_plural = "Widgets das Visões"
        ordering = ['position']

    def __str__(self):
        return f"{self.name} na visão {self.visao.name}"

