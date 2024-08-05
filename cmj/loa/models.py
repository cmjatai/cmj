from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.deletion import PROTECT, CASCADE
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Parlamentar


PERCENTAGE_VALIDATOR = [MinValueValidator(0), MaxValueValidator(100)]


class Loa(models.Model):

    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'))

    materia = models.OneToOneField(
        MateriaLegislativa,
        blank=True, null=True, default=None,
        verbose_name=_('Matéria Legislativa'),
        related_name='loa',
        on_delete=PROTECT)

    receita_corrente_liquida = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Receita Corrente Líquida'),
    )

    perc_disp_total = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Global da RCL (%)'),
    )

    perc_disp_saude = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Saúde da RCL (%)'),
    )

    perc_disp_diversos = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Diversos da RCL (%)'),
    )

    disp_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Global da RCL (R$)'),
    )

    disp_saude = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Saúde da RCL (R$)'),
    )

    disp_diversos = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Diversos da RCL (R$)'),
    )

    parlamentares = models.ManyToManyField(
        Parlamentar,
        through='LoaParlamentar',
        related_name='loa_set',

        verbose_name=_('Parlamentares'),
        through_fields=(
            'loa',
            'parlamentar'))

    publicado = models.BooleanField(
        default=False, verbose_name=_('Publicado?'))

    #descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Loa - Emendas Impositivas')
        verbose_name_plural = _('Loa - Emendas Impositivas')
        ordering = ['-id']

    def __str__(self):
        return f'LOA {self.ano} - {self.materia}'


class LoaParlamentar(models.Model):

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('Loa - Emendas Impositivas'),
        related_name='loaparlamentar_set',
        on_delete=CASCADE)

    parlamentar = models.ForeignKey(
        Parlamentar,
        related_name='loaparlamentar_set',
        verbose_name=_('Parlamentar - Emendas Impositivas'),
        on_delete=CASCADE)

    disp_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Global da RCL (R$)'),
    )

    disp_saude = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Saúde da RCL (R$)'),
    )

    disp_diversos = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_('Disp. Diversos da RCL (R$)'),
    )

    def __str__(self):
        return f'{self.parlamentar} - {self.disp_total} - {self.disp_saude} - {self.disp_diversos}'

    class Meta:
        verbose_name = _('Valores do Parlamentar')
        verbose_name_plural = _('Valores dos Parlamentares')
        ordering = ['id']


class EmendaLoa(models.Model):

    SAUDE = 10
    DIVERSOS = 99
    TIPOEMENDALOA_CHOICE = (
        (SAUDE, _('Saúde')),
        (DIVERSOS, _('Áreas Diversas'))
    )

    PROPOSTA = 10
    APROVACAO_LEGISLATIVA = 20
    APROVACAO_LEGAL = 30
    IMPEDIMENTO_TECNICO = 40
    FASE_CHOICE = (
        (PROPOSTA, _('Proposta Legislativa')),
        (APROVACAO_LEGISLATIVA, _('Aprovada no Poder Legislativo')),
        (APROVACAO_LEGAL, _('Aprovada')),
        (IMPEDIMENTO_TECNICO, _('Impedimento Técnico'))
    )

    tipo = models.PositiveSmallIntegerField(
        choices=TIPOEMENDALOA_CHOICE,
        default=99, verbose_name=_('Área de aplicação'))

    fase = models.PositiveSmallIntegerField(
        choices=FASE_CHOICE,
        default=10, verbose_name=_('Fase'))

    finalidade = models.TextField(_("Finalidade"))

    loa = models.ForeignKey(
        Loa,
        verbose_name=_('Loa - Emendas Impositivas'),
        related_name='emendaloa_set',
        on_delete=CASCADE)

    materia = models.OneToOneField(
        MateriaLegislativa,
        blank=True, null=True, default=None,
        verbose_name=_('Matéria Legislativa'),
        # related_name='emendaloa',
        on_delete=PROTECT)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor Global da Emenda (R$)'),
    )

    parlamentares = models.ManyToManyField(
        Parlamentar,
        through='EmendaLoaParlamentar',
        related_name='emendaloa_set',

        verbose_name=_('Parlamentares'),
        through_fields=(
            'emendaloa',
            'parlamentar'))

    def __str__(self):
        valor_str = formats.number_format(self.valor)
        return f'R$ {valor_str} - {self.finalidade}'

    class Meta:
        verbose_name = _('Emenda Impositiva')
        verbose_name_plural = _('Emendas Impositivas')
        ordering = ['id']


class EmendaLoaParlamentar(models.Model):

    emendaloa = models.ForeignKey(
        EmendaLoa,
        verbose_name=_('Emenda Impositiva'),
        related_name='emendaloaparlamentar_set',
        on_delete=CASCADE)

    parlamentar = models.ForeignKey(
        Parlamentar,
        related_name='emendaloaparlamentar_set',
        verbose_name=_('Parlamentar'),
        on_delete=CASCADE)

    valor = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name=_('Valor por Parlamentar (R$)'),
    )

    def __str__(self):
        valor_str = formats.number_format(self.valor)
        return f'R$ {valor_str} - {self.parlamentar.nome_parlamentar}'

    class Meta:
        verbose_name = _('Participação Parlamentar na Emenda Impositiva')
        verbose_name_plural = _(
            'Participações Parlamentares na Emenda Impositiva')
        ordering = ['id']
