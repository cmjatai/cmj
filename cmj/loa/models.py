from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.deletion import PROTECT, CASCADE
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
