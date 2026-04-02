from decimal import Decimal

from django.db import models
from django.db.models import manager
from django.db.models.deletion import CASCADE, PROTECT
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from cmj.loa.models.registrocontabil import EmendaLoaRegistroContabil
from cmj.utils import PERCENTAGE_VALIDATOR, quantize


class Agrupamento(models.Model):

    loa = models.ForeignKey(
        "loa.Loa",
        verbose_name=_("LOA"),
        related_name="agrupamento_set",
        on_delete=PROTECT,
    )

    nome = models.CharField(verbose_name=_("Nome do Agrupamento"), max_length=256)

    emendas = models.ManyToManyField(
        "loa.EmendaLoa",
        through="AgrupamentoEmendaLoa",
        related_name="agrupamento_set",
        verbose_name=_("Emendas Impositivas/Modificativas"),
        through_fields=("agrupamento", "emendaloa"),
    )

    despesas = models.ManyToManyField(
        "loa.Despesa",
        through="AgrupamentoRegistroContabil",
        related_name="agrupamento_set",
        verbose_name=_("Registro Contabeis Agrupamento"),
        through_fields=("agrupamento", "despesa"),
    )

    class Meta:
        verbose_name = _("Agrupamento de Emenda Impositiva/Modificativas")
        verbose_name_plural = _("Agrupamentos de Emendas Impositivas/Modificativas")
        ordering = ["id"]

    def __str__(self):
        return self.nome

    def sync(self):
        registros = self.agrupamentoregistrocontabil_set.all()

        for emenda in self.emendas.all():
            emenda.registrocontabil_set.all().delete()

            deducoes = []
            insercoes = []
            soma_zero = Decimal("0.00")
            for r in registros:
                elrc = EmendaLoaRegistroContabil()
                elrc.emendaloa = emenda
                elrc.despesa = r.despesa
                elrc.valor = quantize(emenda.valor * r.percentual / Decimal(100))
                elrc.save()

                soma_zero += r.percentual

                if r.percentual < Decimal("0.00"):
                    deducoes.append(elrc)
                else:
                    insercoes.append(elrc)

            if soma_zero == Decimal("0.00"):
                sum_deducoes = sum(map(lambda x: x.valor, deducoes))
                sum_insercoes = sum(map(lambda x: x.valor, insercoes))

                if abs(sum_deducoes) != emenda.valor and deducoes:
                    resto = emenda.valor + sum_deducoes
                    deducoes[-1].valor = deducoes[-1].valor - resto
                    deducoes[-1].save()

                if abs(sum_insercoes) != emenda.valor and insercoes:
                    resto = emenda.valor - sum_insercoes
                    insercoes[-1].valor = insercoes[-1].valor + resto
                    insercoes[-1].save()

            print()


class AgrupamentoEmendaLoa(models.Model):
    agrupamento = models.ForeignKey(
        "loa.Agrupamento",
        verbose_name=_("Agrupamento de Emenda Impositiva"),
        related_name="agrupamentoemendaloa_set",
        on_delete=CASCADE,
    )

    emendaloa = models.OneToOneField(
        "loa.EmendaLoa",
        verbose_name=_("Emenda Impositiva"),
        related_name="agrupamentoemendaloa",
        on_delete=CASCADE,
    )

    class Meta:
        verbose_name = _("Agrupamento de Emenda Impositiva")
        verbose_name_plural = _("Agrupamentos de Emendas Impositivas")
        ordering = ["id"]

        unique_together = (
            (
                "agrupamento",
                "emendaloa",
            ),
        )


class AgrupamentoRegistroContabilManager(manager.Manager):

    use_for_related_fields = True

    def all_deducoes(self):
        qs = self.get_queryset()
        qs = qs.filter(percentual__lt=Decimal("0.00"))
        return qs

    def all_insercoes(self):
        qs = self.get_queryset()
        qs = qs.filter(percentual__gt=Decimal("0.00"))
        return qs


class AgrupamentoRegistroContabil(models.Model):

    DEDUCAO = 10
    INSERCAO = 20

    OPERACAO_CHOICE = ((DEDUCAO, _("Dedução")), (INSERCAO, _("Inserção")))

    objects = AgrupamentoRegistroContabilManager()

    agrupamento = models.ForeignKey(
        'loa.Agrupamento',
        verbose_name=_("Agrupamento de Emenda Impositiva"),
        related_name="agrupamentoregistrocontabil_set",
        on_delete=CASCADE,
    )

    despesa = models.ForeignKey(
        "loa.Despesa",
        blank=True,
        null=True,
        default=None,
        related_name="agrupamentoregistrocontabil_set",
        verbose_name=_("Despesa"),
        on_delete=CASCADE,
    )

    operacao = models.PositiveSmallIntegerField(
        choices=OPERACAO_CHOICE, default=10, verbose_name=_("Operação")
    )

    percentual = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("100.00"),
        validators=PERCENTAGE_VALIDATOR,
        verbose_name=_("Percentual do Valor da Emenda"),
    )

    class Meta:
        verbose_name = _("Registro Contábil de Dedução e Inserção em Emendas")
        verbose_name_plural = _("Registros Contábeis de Dedução e Inserção em Emendas")
        ordering = ["id"]

        unique_together = (
            (
                "agrupamento",
                "despesa",
            ),
        )

    def __str__(self):
        percentual_str = formats.number_format(self.percentual, force_grouping=True)
        return f"{percentual_str}% - {self.despesa}"

    @property
    def str_percentual(self):
        return formats.number_format(self.percentual, force_grouping=True)
