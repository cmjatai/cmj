import logging
import re
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import manager
from django.db.models.deletion import CASCADE, PROTECT
from django.db.models.fields.json import JSONField
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from cmj.loa.models.m_registrocontabil import EmendaLoaRegistroContabil
from cmj.utils import PERCENTAGE_VALIDATOR, quantize
from cmj.utils.genia.loa_agrupamento import IAEmentaEmendaColetiva
from sapl.parlamentares.models import Parlamentar

logger = logging.getLogger(__name__)


class Agrupamento(models.Model):

    loa = models.ForeignKey(
        "loa.Loa",
        verbose_name=_("LOA"),
        related_name="agrupamento_set",
        on_delete=PROTECT,
    )

    nome = models.CharField(verbose_name=_("Nome do Agrupamento"), max_length=256)

    finalidade = models.TextField(verbose_name=_("Finalidade"), blank=True, default="")

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

    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    class Meta:
        verbose_name = _("Agrupamento de Emenda Impositiva/Modificativas")
        verbose_name_plural = _("Agrupamentos de Emendas Impositivas/Modificativas")
        ordering = ["id"]

    def __str__(self):
        return self.nome

    @property
    def finalidade_format(self):
        try:
            finalidade = self.finalidade or ""

            while len(finalidade) > 0 and (re.match(r"[^\w\)\$]", finalidade[-1])):
                finalidade = finalidade[:-1]

            return finalidade
        except Exception:
            return ""

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

        try:
            self.update_finalidade_com_ia()
        except Exception as e:
            logger.error("Erro ao atualizar finalidade com IA: %s", e)

    def update_finalidade_com_ia(self):

        # verifica se todas as emendas são tem a mesma unidade e entidade
        emendas = list(self.emendas.values("unidade", "entidade"))
        if not emendas:
            raise ValueError("Não há emendas para este agrupamento")
        first_unidade = emendas[0]["unidade"]
        first_entidade = emendas[0]["entidade"]
        error = False
        for e in emendas:
            if e["unidade"] != first_unidade or e["entidade"] != first_entidade:
                error = True
                break

        if error:
            self.finalidade = ""
            self.save(update_fields=["finalidade"])
            raise ValueError(
                "É necessário que todas as emendas possuam a mesma unidade e entidade."
            )
        try:
            ia = IAEmentaEmendaColetiva(
                [str(e.finalidade_format) for e in self.emendas.all()]
            )
            self.finalidade = ia.gerar_finalidade_global()
            if not self.finalidade:
                self.finalidade = ""
            self.save(update_fields=["finalidade"])
        except Exception as e:
            logger.error("Erro ao atualizar finalidade com IA: %s", e)
            self.finalidade = ""
            self.save(update_fields=["finalidade"])

    def preparar_dados_para_coletiva(self):

        # a chave de agrupamento de emendas é a unidade + entidade, onde unidade nunca é nula mas a entidade pode ser nula

        emendas_coletivas = {}

        for emenda in self.emendas.all():
            if not emenda.permite_juncao_coletiva:
                continue

            key = (emenda.unidade, emenda.entidade)
            if key not in emendas_coletivas:
                emendas_coletivas[key] = {
                    "emendas": [],
                    "insercoes": {},
                    "deducoes": {},
                    "parlamentares": {},
                    "total_via_parlamentares": Decimal("0.00"),
                }
            emendas_coletivas[key]["emendas"].append(emenda)

            insercoes = emendas_coletivas[key]["insercoes"]
            deducoes = emendas_coletivas[key]["deducoes"]
            parlamentares = emendas_coletivas[key]["parlamentares"]
            total_via_parlamentares = emendas_coletivas[key]["total_via_parlamentares"]

            for r in emenda.registrocontabil_set.all_insercoes():
                insercoes[r.despesa] = (
                    insercoes.get(r.despesa, Decimal("0.00")) + r.valor
                )
            for r in emenda.registrocontabil_set.all_deducoes():
                deducoes[r.despesa] = deducoes.get(r.despesa, Decimal("0.00")) + r.valor

            for elp in emenda.emendaloaparlamentar_set.all():
                if elp.parlamentar not in parlamentares:
                    parlamentares[elp.parlamentar] = {
                        "valor": Decimal("0.00"),
                        "prefixo_finalidade": emenda.prefixo_finalidade,
                        "finalidade": [],
                    }
                parlamentares[elp.parlamentar]["valor"] += elp.valor
                parlamentares[elp.parlamentar]["finalidade"].append(
                    f"<strong>R$ {emenda.str_valor}</strong> - {emenda.prefixo_finalidade} {emenda.finalidade_format}"
                )
                total_via_parlamentares += elp.valor

            emendas_coletivas[key]["total_via_parlamentares"] = total_via_parlamentares

        # ordenar parlamentares por nome_parlamentar
        for key in emendas_coletivas:
            parlamentares = emendas_coletivas[key]["parlamentares"]
            emendas_coletivas[key]["parlamentares"] = dict(
                sorted(parlamentares.items(), key=lambda item: item[0].nome_parlamentar)
            )

        # criar finalidade agregada para cada agrupamento via I.A.
        # ia = IAEmentaEmendaColetiva()
        # for key in emendas_coletivas:
        #    emendas = emendas_coletivas[key]["emendas"]
        #    finalidades = [emenda.finalidade for emenda in emendas]
        #    finalidade_agregada = ia.gerar_finalidade_global(finalidades)
        #    emendas_coletivas[key]["finalidade_agregada"] = finalidade_agregada

        return [
            {
                "object": self,
                "emendas": value["emendas"],
                "unidade": unidade,
                "entidade": entidade,
                "finalidade_agregada": value.get("finalidade_agregada", None),
                "bairro": value["emendas"][0].bairro if value["emendas"] else None,
                "total_via_parlamentares": value["total_via_parlamentares"],
                "parlamentares": Parlamentar.objects.filter(
                    id__in=[p.id for p in value["parlamentares"].keys()]
                ),
                "parlamentares_list_values": value["parlamentares"],
                "insercoes": value["insercoes"],
                "deducoes": value["deducoes"],
            }
            for (unidade, entidade), value in emendas_coletivas.items()
        ]


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
        "loa.Agrupamento",
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
