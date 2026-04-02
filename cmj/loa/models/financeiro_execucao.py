from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Sum
from django.db.models.deletion import CASCADE, PROTECT
from django.db.models.fields.json import JSONField
from django.utils import formats
from django.utils.translation import gettext_lazy as _


class DespesaPaga(models.Model):

    mapeamento = {
        "Código:": "codigo",
        "Código": "codigo",
        "Data:": "data",
        "Data": "data",
        "Banco:": "banco",
        "Banco": "banco",
        "Agência:": "agencia",
        "Agência": "agencia",
        "Conta Bancária:": "conta",
        "Conta": "conta",
        "Tipo do Documento:": "tipo",
        "Tipo do Documento": "tipo",
        "Nº do Documento:": "numero_documento",
        "Número do Documento": "numero_documento",
        "Número da Licitação:": "numero_licitacao",
        "Código Empenho:": "empenho",
        "Elemento:": "elemento",
        "Sub Elemento:": "subelemento",
        "Unidade Financeira:": "unidade",
        "Unidade Financeira": "unidade",
        "Fonte de Recursos:": "fonte",
        "Fonte de Recursos": "fonte",
        "Historico:": "historico",
        "Número": "numero_emissao",
        "Série": "serie",
        "Data de Emissão": "data_emissao",
        "Tipo": "tipo_emissao",
        "Valor": "valor",
    }

    codigo = models.TextField(verbose_name=_("Código"))

    cpfcnpj = models.TextField(
        verbose_name=_("CpfCNPJ"), blank=True, null=True, default=None
    )
    nome = models.TextField(verbose_name=_("Nome"), blank=True, null=True, default=None)
    historico = models.TextField(
        verbose_name=_("Histórico"), blank=True, null=True, default=None
    )
    tipo = models.TextField(verbose_name=_("Tipo"), blank=True, null=True, default=None)

    data = models.DateField(blank=True, null=True, verbose_name=_("Data"))

    orgao = models.ForeignKey(
        "loa.Orgao",
        related_name="despesapaga_set",
        verbose_name=_("Órgão"),
        on_delete=PROTECT,
    )

    unidade = models.ForeignKey(
        "loa.UnidadeOrcamentaria",
        blank=True,
        null=True,
        default=None,
        related_name="despesapaga_set",
        verbose_name=_("Unidade Financeira"),
        on_delete=PROTECT,
    )

    natureza = models.ForeignKey(
        "loa.Natureza",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Natureza"),
        related_name="despesapaga_set",
        on_delete=PROTECT,
    )

    fonte = models.ForeignKey(
        "loa.Fonte",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Fonte"),
        related_name="despesapaga_set",
        on_delete=PROTECT,
    )

    valor = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor (R$)"),
    )
    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    class Meta:
        verbose_name = _("Despesa Paga")
        verbose_name_plural = _("Despesas Pagas")
        ordering = ["id"]


class Empenho(models.Model):

    mapeamento = {
        "Código:": "codigo",
        "Código": "codigo",
        "Data:": "data",
        "Data": "data",
        "Fornecedor:": "nome",
        "Fornecedor": "nome",
        "Órgão:": "orgao",
        "Órgão": "orgao",
        "Unidade:": "unidade",
        "Unidade": "unidade",
        "Função:": "funcao",
        "Função": "funcao",
        "Sub-Função:": "subfuncao",
        "Sub-Função": "subfuncao",
        "Programa:": "programa",
        "Programa": "programa",
        "Projeto / Atividade:": "acao",
        "Projeto / Atividade": "acao",
        "Elemento:": "natureza",
        "Sub-Elemento:": "natureza",
        "Elemento": "natureza",
        "Sub-Elemento": "natureza",
        "Fonte de Recursos:": "fonte",
        "Fonte de Recursos": "fonte",
        "Modalidade:": "modalidade",
        "Número da Licitação:": "numero_licitacao",
        "Historico:": "historico",
        "Dotação:": "dotacao",
        "Valor Empenhado": "valor_empenhado",
        "Valor Anulado": "valor_anulado",
        "Valor Liquidado": "valor_liquidado",
        "Valor Pago Bruto": "valor_pago_bruto",
    }

    codigo = models.PositiveIntegerField(verbose_name=_("Código"))

    cpfcnpj = models.TextField(
        verbose_name=_("CpfCNPJ"), blank=True, null=True, default=None
    )
    nome = models.TextField(verbose_name=_("Nome"), blank=True, null=True, default=None)
    tipo = models.TextField(verbose_name=_("Tipo"), blank=True, null=True, default=None)

    data = models.DateField(blank=True, null=True, verbose_name=_("Data"))

    modalidade = models.TextField(
        verbose_name=_("Modalidade"), blank=True, null=True, default=None
    )
    numero_licitacao = models.TextField(
        verbose_name=_("Número da Licitação"), blank=True, null=True, default=None
    )

    historico = models.TextField(
        verbose_name=_("Histórico"), blank=True, null=True, default=None
    )
    dotacao = models.TextField(
        verbose_name=_("Dotação"), blank=True, null=True, default=None
    )

    processo = models.TextField(
        verbose_name=_("Processo"), blank=True, null=True, default=None
    )

    orgao = models.ForeignKey(
        "loa.Orgao",
        related_name="empenho_set",
        verbose_name=_("Órgão"),
        on_delete=PROTECT,
    )

    unidade = models.ForeignKey(
        "loa.UnidadeOrcamentaria",
        blank=True,
        null=True,
        default=None,
        related_name="empenho_set",
        verbose_name=_("Unidade Financeira"),
        on_delete=PROTECT,
    )

    funcao = models.ForeignKey(
        "loa.Funcao",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Função"),
        related_name="empenho_set",
        on_delete=PROTECT,
    )

    subfuncao = models.ForeignKey(
        "loa.SubFuncao",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Subfunção"),
        related_name="empenho_set",
        on_delete=PROTECT,
    )

    programa = models.ForeignKey(
        "loa.Programa",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Programa"),
        related_name="empenho_set",
        on_delete=PROTECT,
    )

    acao = models.ForeignKey(
        "loa.Acao",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Ação"),
        related_name="empenho_set",
        on_delete=PROTECT,
    )

    natureza = models.ForeignKey(
        "loa.Natureza",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Natureza"),
        related_name="empenho_set",
        on_delete=PROTECT,
    )

    fonte = models.ForeignKey(
        "loa.Fonte",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Fonte"),
        related_name="empenho_set",
        on_delete=PROTECT,
    )

    valor_empenhado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor Empenhado (R$)"),
    )

    valor_anulado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor Anulado (R$)"),
    )
    valor_liquidado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor Liquidado (R$)"),
    )

    valor_pago_bruto = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor Pago (Bruto) (R$)"),
    )

    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    class Meta:
        verbose_name = _("Empenho")
        verbose_name_plural = _("Empenhos")
        ordering = ["id"]

    def __str__(self):
        return f"{self.codigo} - {self.nome} - R$ {self.valor_empenhado}"

    @property
    def str_valor_empenhado(self):
        return formats.number_format(self.valor_empenhado, force_grouping=True)

    @property
    def str_valor_anulado(self):
        return formats.number_format(self.valor_anulado, force_grouping=True)

    @property
    def str_valor_liquidado(self):
        return formats.number_format(self.valor_liquidado, force_grouping=True)

    @property
    def str_valor_pago_bruto(self):
        return formats.number_format(self.valor_pago_bruto, force_grouping=True)


class EmpenhoEmendaAjusteManager(models.Manager):
    use_for_related_fields = True

    def aggregate_sum_dos_empenhos(self):
        se = self.aggregate(
            valor_empenhado=Sum("empenho__valor_empenhado"),
            valor_anulado=Sum("empenho__valor_anulado"),
            valor_liquidado=Sum("empenho__valor_liquidado"),
            valor_pago_bruto=Sum("empenho__valor_pago_bruto"),
        )
        return se


class EmpenhoEmendaAjuste(models.Model):

    objects = EmpenhoEmendaAjusteManager()

    emendaloa = models.ForeignKey(
        "loa.EmendaLoa",
        verbose_name=_("Emenda Impositiva"),
        related_name="empenhoemendaajuste_set",
        on_delete=CASCADE,
        blank=True,
        null=True,
        default=None,
    )

    ajuste = models.ForeignKey(
        "loa.RegistroAjusteLoa",
        verbose_name=_("Registro de Ajuste Técnico"),
        related_name="empenhoemendaajuste_set",
        on_delete=CASCADE,
        blank=True,
        null=True,
        default=None,
    )

    empenho = models.ForeignKey(
        "loa.Empenho",
        verbose_name=_("Empenho"),
        related_name="empenhoemendaajuste_set",
        on_delete=CASCADE,
    )

    class Meta:
        verbose_name = _("Empenho de Emenda e/ou Ajuste Técnico")
        verbose_name_plural = _("Empenhos de Emendas e/ou Ajustes Técnicos")
        ordering = ["id"]
        unique_together = (
            (
                "emendaloa",
                "ajuste",
                "empenho",
            ),
        )


class ReceitaArrecadada(models.Model):

    data = models.DateField(blank=True, null=True, verbose_name=_("Data"))

    tipo = models.TextField(verbose_name=_("Tipo"), blank=True, null=True, default=None)

    historico = models.TextField(
        verbose_name=_("Histórico"), blank=True, null=True, default=None
    )

    receita = models.ForeignKey(
        "loa.ReceitaOrcamentaria",
        related_name="receitaarrecadada_set",
        verbose_name=_("Receita Orçamentária"),
        on_delete=PROTECT,
    )

    valor = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor (R$)"),
    )

    class Meta:
        verbose_name = _("Receita Arrecadada")
        verbose_name_plural = _("Receitas Arrecadadas")
        ordering = ["id"]
