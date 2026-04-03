from decimal import Decimal

from django.db import models
from django.db.models.deletion import CASCADE, PROTECT
from django.utils.translation import gettext_lazy as _

from cmj.loa.services.s_loa import LoaService
from cmj.utils import PERCENTAGE_VALIDATOR
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Parlamentar


class Loa(models.Model):

    service = LoaService()

    ano = models.PositiveSmallIntegerField(verbose_name=_("Ano"))

    materia = models.OneToOneField(
        MateriaLegislativa,
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Matéria Legislativa"),
        related_name="loa",
        on_delete=PROTECT,
    )

    rcl_previa = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Receita Corrente Líquida - Prévia (R$)"),
    )

    receita_corrente_liquida = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Receita Corrente Líquida - RCL (R$)"),
    )

    perc_disp_total = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_("Disp. Global da RCL (%)"),
    )

    perc_disp_saude = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_("Disp. Saúde da RCL (%)"),
    )

    perc_disp_diversos = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_("Disp. Diversos da RCL (%)"),
    )

    disp_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Disp. Global da RCL (R$)"),
    )

    disp_saude = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Disp. Saúde da RCL (R$)"),
    )

    disp_diversos = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Disp. Diversos da RCL (R$)"),
    )

    parlamentares = models.ManyToManyField(
        Parlamentar,
        through="LoaParlamentar",
        related_name="loa_set",
        verbose_name=_("Parlamentares"),
        through_fields=("loa", "parlamentar"),
    )

    yaml_obs = models.TextField(
        verbose_name=_("Observações de Rodapé (yaml format)"),
        blank=True,
        null=True,
        default="",
    )

    publicado = models.BooleanField(default=False, verbose_name=_("Publicado?"))

    # descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    despesa_default_deducao_saude = models.ForeignKey(
        "Despesa",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Despesa Default Dedução Saúde"),
        related_name="loa_despesa_default_deducao_saude",
        on_delete=PROTECT,
    )

    despesa_default_deducao_diversos = models.ForeignKey(
        "Despesa",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Despesa Default Dedução Diversos"),
        related_name="loa_despesa_default_deducao_diversos",
        on_delete=PROTECT,
    )

    despesa_default_deducao_educacao = models.ForeignKey(
        "Despesa",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Despesa Default Dedução Educação"),
        related_name="loa_despesa_default_deducao_educacao",
        on_delete=PROTECT,
    )

    class Meta:
        verbose_name = _("LOA")
        verbose_name_plural = _("LOAs")
        ordering = ["-id"]
        permissions = (("view_despesasexecutadas", _("View Despesas Executadas")),)

    def __str__(self):
        nj = self.materia.normajuridica() if self.materia else ""
        descr = nj or (self.materia or "")
        return f"LOA {self.ano} - {descr}"

    def update_disponibilidades(self):
        Loa.service.update_disponibilidades(self)


class LoaParlamentar(models.Model):

    loa = models.ForeignKey(
        Loa, verbose_name=_("LOA"), related_name="loaparlamentar_set", on_delete=CASCADE
    )

    parlamentar = models.ForeignKey(
        Parlamentar,
        related_name="loaparlamentar_set",
        verbose_name=_("Parlamentar - Emendas Impositivas"),
        on_delete=CASCADE,
    )

    disp_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Disp. Global da RCL (R$)"),
    )

    disp_saude = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Disp. Saúde da RCL (R$)"),
    )

    disp_diversos = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Disp. Diversos da RCL (R$)"),
    )

    def __str__(self):
        return f"{self.parlamentar} - {self.disp_total} - {self.disp_saude} - {self.disp_diversos}"

    class Meta:
        verbose_name = _("Valores do Parlamentar")
        verbose_name_plural = _("Valores dos Parlamentares")
        ordering = ["id"]
