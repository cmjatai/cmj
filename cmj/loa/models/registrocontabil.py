from decimal import Decimal

from django.db import models
from django.db.models import manager
from django.db.models.deletion import CASCADE, PROTECT
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from cmj.utils import (
    run_sql,
)


class EmendaLoaRegistroContabilManager(manager.Manager):

    use_for_related_fields = True

    def all_deducoes(self):
        qs = self.get_queryset()
        qs = qs.filter(valor__lt=Decimal("0.00"))
        return qs

    def all_insercoes(self):
        qs = self.get_queryset()
        qs = qs.filter(valor__gt=Decimal("0.00"))
        return qs


class EmendaLoaRegistroContabil(models.Model):

    objects = EmendaLoaRegistroContabilManager()

    emendaloa = models.ForeignKey(
        'loa.EmendaLoa',
        verbose_name=_("Emenda Impositiva"),
        related_name="registrocontabil_set",
        on_delete=CASCADE,
    )

    despesa = models.ForeignKey(
        'loa.Despesa',
        blank=True,
        null=True,
        default=None,
        related_name="registrocontabil_set",
        verbose_name=_("Despesa"),
        on_delete=PROTECT,
    )

    valor = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor (R$)"),
    )

    def __str__(self):
        return f"R$ {self.str_valor} - {self.despesa}"

    @property
    def str_valor(self):
        str_valor = formats.number_format(self.valor, force_grouping=True)
        str_valor = (
            " " * (self._meta.get_field("valor").max_digits - len(str_valor))
            + str_valor
        )
        return str_valor

    def delete(self, *args, **kwargs):
        # remove emenda de agrupamento que possa pertercer sem causar recursividade do agrupamentoemendaloa_pre_delete
        run_sql(
            f"DELETE FROM loa_agrupamentoemendaloa WHERE emendaloa_id = {self.emendaloa.id}"
        )
        # run_sql acima substitui: AgrupamentoEmendaLoa.objects.filter(emendaloa=self.emendaloa).delete()

        return super().delete(*args, **kwargs)

    class Meta:
        verbose_name = _("Registro Contábil de Dedução e Inserção em Emendas")
        verbose_name_plural = _("Registros Contábeis de Dedução e Inserção em Emendas")
        ordering = ["id"]

        unique_together = (
            (
                "emendaloa",
                "despesa",
            ),
        )
