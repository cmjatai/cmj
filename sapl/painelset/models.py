from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Tela(models.Model):

    timer = models.BooleanField(
        verbose_name=_('Tela de Timer Individual'), default=False)

    cols = models.PositiveSmallIntegerField(
        default=12,
        validators=[
            MaxValueValidator(30),
            MinValueValidator(3)
        ]
    )

    rows = models.PositiveSmallIntegerField(
        default=30,
        validators=[
            MaxValueValidator(30),
            MinValueValidator(3)
        ]
    )

    class Meta:
        pass


class ComponenteBase(models.Model):

    descricao = models.CharField(
        max_length=50, default='',
        verbose_name='Descrição de Componente de Tela')

    name = models.CharField(
        max_length=50, default='', unique=True,
        verbose_name='Nome Vue do Componente')

    class Meta:
        pass


class ComponenteTela(models.Model):

    componente = models.ForeignKey(
        ComponenteBase,
        blank=True, null=True, default=None,
        verbose_name=_('Componente Base'),
        on_delete=models.PROTECT)

    tela = models.ForeignKey(
        Tela,
        blank=True, null=True, default=None,
        verbose_name=_('Tela do Componente'),
        on_delete=models.PROTECT)

    x = models.PositiveSmallIntegerField(
        default=0,
    )

    y = models.PositiveSmallIntegerField(
        default=0,
    )

    w = models.PositiveSmallIntegerField(
        default=5,
    )

    h = models.PositiveSmallIntegerField(
        default=2,
    )

    class Meta:
        pass


class PainelSET(models.Model):

    descricao = models.CharField(
        max_length=50, default='',
        verbose_name='Descrição do Conjunto de Paineis')

    class Meta:
        ordering = ('descricao',)
        verbose_name = _('Conjunto de Paineis')
        verbose_name_plural = _('Conjuntos de Paineis')

    def __str__(self):
        return self.descricao


class Painel(models.Model):

    descricao = models.CharField(
        max_length=50, default='',
        verbose_name='Descrição do Painel')

    painelset = models.ForeignKey(
        PainelSET,
        verbose_name=_('Conjunto de Paineis'),
        on_delete=models.PROTECT)

    tela = models.ForeignKey(
        Tela,
        blank=True, null=True, default=None,
        related_name='painel_tela_set',
        verbose_name=_('Tela Associada ao Painel'),
        on_delete=models.PROTECT)

    timer = models.ForeignKey(
        Tela,
        blank=True, null=True, default=None,
        related_name='painel_timer_set',
        verbose_name=_('Tela de Timer Individual de Falas'),
        on_delete=models.PROTECT)


"""
    PAINEL_TYPES = (
        ('C', 'Completo'),
        ('P', 'Parlamentares'),
        ('V', 'Votação'),
        ('M', 'Mensagem'),
    )

    aberto = models.BooleanField(verbose_name=_('Abrir painel'), default=False)
    data_painel = models.DateField(verbose_name=_('Data painel'))
    mostrar = models.CharField(max_length=1,
                               choices=PAINEL_TYPES, default='C')

    class Meta:
        ordering = ('-data_painel',)

    def __str__(self):
        return str(self.aberto) + ":" + self.data_painel.strftime("%d/%m/%Y")


class Cronometro(models.Model):
    CRONOMETRO_TYPES = (
        ('A', _('Aparte')),
        ('D', _('Discurso')),
        ('O', _('Ordem do dia')),
        ('C', _('Considerações finais'))
    )

    CRONOMETRO_STATUS = (
        ('I', 'Start'),
        ('R', 'Reset'),
        ('S', 'Stop'),
    )

    status = models.CharField(
        max_length=1,
        verbose_name=_('Status do cronômetro'),
        choices=CRONOMETRO_STATUS,
        default='S')
    data_cronometro = models.DateField(verbose_name=_('Data do cronômetro'))
    tipo = models.CharField(
        max_length=1, choices=CRONOMETRO_TYPES,
        verbose_name=_('Tipo Cronômetro'))

    class Meta:
        ordering = ('-data_cronometro',)
"""
