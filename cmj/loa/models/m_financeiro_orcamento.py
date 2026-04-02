from decimal import Decimal

from django.db import models
from django.db.models.deletion import PROTECT
from django.utils.translation import gettext_lazy as _


class ElementoBase(models.Model):

    loa = models.ForeignKey(
        "loa.Loa", verbose_name=_("Loa"), related_name="+", on_delete=PROTECT
    )

    codigo = models.TextField(verbose_name=_("Código"))

    especificacao = models.CharField(
        max_length=256, verbose_name=_("Especificação"), default="", blank=True
    )

    # metadata = JSONField(
    #    verbose_name=_('Metadados'),
    #    blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.codigo} - {self.especificacao}"


class Orgao(ElementoBase):

    class Meta:
        verbose_name = _("Órgão")
        verbose_name_plural = _("Órgãos")
        ordering = ["codigo"]


class UnidadeOrcamentaria(ElementoBase):

    orgao = models.ForeignKey(
        Orgao,
        verbose_name=_("Órgão"),
        related_name="unidadeorcamentaria_set",
        on_delete=PROTECT,
    )

    recebe_emenda_impositiva = models.BooleanField(
        default=False,
        verbose_name=_("Recebe Verbas Emenda Impositiva"),
    )

    SAUDE_CHOICE = 10
    EDUCACAO_CHOICE = 20
    ASSISTENCIA_SOCIAL_CHOICE = 30
    SEGURANCA_PUBLICA_CHOICE = 40
    CULTURA_CHOICE = 50
    ESPORTE_CHOICE = 60
    OUTROS_CHOICE = 70

    area = models.PositiveSmallIntegerField(
        choices=(
            (SAUDE_CHOICE, _("Saúde")),
            (EDUCACAO_CHOICE, _("Educação")),
            (ASSISTENCIA_SOCIAL_CHOICE, _("Assistência Social")),
            (SEGURANCA_PUBLICA_CHOICE, _("Segurança Pública")),
            (CULTURA_CHOICE, _("Cultura")),
            (ESPORTE_CHOICE, _("Esporte")),
            (OUTROS_CHOICE, _("Outros")),
        ),
        default=OUTROS_CHOICE,
        verbose_name=_("Tipo Geral"),
    )

    class Meta:
        verbose_name = _("Unidade Orçamentária")
        verbose_name_plural = _("Unidades Orçamentárias")
        ordering = ["codigo"]


class Funcao(ElementoBase):

    class Meta:
        verbose_name = _("Função")
        verbose_name_plural = _("Funções")
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.especificacao} ({self.loa.ano})"


class SubFuncao(ElementoBase):

    funcao = models.ForeignKey(
        Funcao, verbose_name=_("Função"), related_name="funcao_set", on_delete=PROTECT
    )

    class Meta:
        verbose_name = _("SubFunção")
        verbose_name_plural = _("SubFunções")
        ordering = ["codigo"]


class Programa(ElementoBase):

    class Meta:
        verbose_name = _("Programa")
        verbose_name_plural = _("Programas")
        ordering = ["codigo"]


class Acao(ElementoBase):

    class Meta:
        verbose_name = _("Ação")
        verbose_name_plural = _("Ações")
        ordering = ["codigo"]


class Fonte(ElementoBase):

    class Meta:
        verbose_name = _("Fonte")
        verbose_name_plural = _("Fontes")
        ordering = ["codigo"]


class Natureza(ElementoBase):

    class Meta:
        verbose_name = _("Natureza")
        verbose_name_plural = _("Naturezas")
        ordering = ["codigo"]


class Despesa(models.Model):

    loa = models.ForeignKey(
        "loa.Loa", verbose_name=_("Loa"), related_name="despesa_set", on_delete=PROTECT
    )

    orgao = models.ForeignKey(
        Orgao, verbose_name=_("Órgão"), related_name="despesa_set", on_delete=PROTECT
    )

    unidade = models.ForeignKey(
        UnidadeOrcamentaria,
        verbose_name=_("Unidade Orçamentária"),
        related_name="despesa_set",
        on_delete=PROTECT,
    )

    funcao = models.ForeignKey(
        Funcao, verbose_name=_("Função"), related_name="despesa_set", on_delete=PROTECT
    )

    subfuncao = models.ForeignKey(
        SubFuncao,
        verbose_name=_("SubFunção"),
        related_name="despesa_set",
        on_delete=PROTECT,
    )

    programa = models.ForeignKey(
        Programa,
        verbose_name=_("Programa"),
        related_name="despesa_set",
        on_delete=PROTECT,
    )

    acao = models.ForeignKey(
        Acao, verbose_name=_("Ação"), related_name="despesa_set", on_delete=PROTECT
    )

    fonte = models.ForeignKey(
        Fonte,
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Fonte"),
        related_name="despesa_set",
        on_delete=PROTECT,
    )

    natureza = models.ForeignKey(
        Natureza,
        verbose_name=_("Natureza"),
        related_name="despesa_set",
        on_delete=PROTECT,
    )

    valor_materia = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor Despesa Matéria (R$)"),
    )

    valor_norma = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor Despesa Norma (R$)"),
    )

    class Meta:
        verbose_name = _("Despesa")
        verbose_name_plural = _("Despesas")
        ordering = ["id"]

        unique_together = (
            (
                "loa",
                "orgao",
                "unidade",
                "funcao",
                "subfuncao",
                "programa",
                "acao",
                "fonte",
                "natureza",
            ),
        )

    def __str__(self):
        dc = DespesaConsulta.objects.get(pk=self.id)
        return str(dc)

    @property
    def consulta(self):
        return DespesaConsulta.objects.get(pk=self.id)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):

        self.clean()

        return models.Model.save(
            self,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def clean(self):

        # Check for instances with null values in unique_together fields.

        from django.core.exceptions import ValidationError

        super().clean()

        for field_tuple in self._meta.unique_together[:]:
            unique_filter = {}
            unique_fields = []
            null_found = False
            for field_name in field_tuple:
                field_value = getattr(self, field_name)
                if getattr(self, field_name) is None:
                    unique_filter["%s__isnull" % field_name] = True
                    null_found = True
                else:
                    unique_filter["%s" % field_name] = field_value
                    unique_fields.append(field_name)
            if null_found:
                unique_queryset = self.__class__.objects.filter(**unique_filter)
                if self.pk:
                    unique_queryset = unique_queryset.exclude(pk=self.pk)
                if unique_queryset.exists():
                    msg = self.unique_error_message(
                        self.__class__, tuple(unique_fields)
                    )
                    raise ValidationError(msg)


class DespesaConsulta(models.Model):

    loa = models.ForeignKey(
        "loa.Loa", verbose_name=_("Loa"), related_name="+", on_delete=PROTECT
    )

    valor_materia = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor Despesa Matéria (R$)"),
    )

    valor_norma = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor Despesa Norma (R$)"),
    )

    codigo = models.TextField(verbose_name=_("Código"))
    especificacao = models.TextField(verbose_name=_("Especificação"))

    cod_orgao = models.TextField(verbose_name=_("Código do Órgão"))
    esp_orgao = models.TextField(verbose_name=_("Órgão"))

    cod_unidade = models.TextField(verbose_name=_("Código da Unidade"))
    esp_unidade = models.TextField(verbose_name=_("Unidade Orçamentária"))

    cod_natureza = models.TextField(verbose_name=_("Código Natureza"))
    esp_natureza = models.TextField(verbose_name=_("Natureza da Despesa"))
    cod_fonte = models.TextField(verbose_name=_("Fonte"))

    class Meta:
        managed = False
        db_table = "loa_despesa_consulta"
        ordering = ("cod_orgao", "cod_unidade", "codigo", "cod_natureza")

    def __str__(self):
        return (
            f"{self.codigo}:{self.cod_natureza}/{self.cod_fonte} - {self.especificacao}"
        )


class ReceitaOrcamentaria(models.Model):

    codigo = models.TextField(verbose_name=_("Código"))

    historico = models.TextField(
        verbose_name=_("Histórico"), blank=True, null=True, default=None
    )

    orgao = models.ForeignKey(
        "loa.Orgao",
        related_name="receitaorcamentaria_set",
        verbose_name=_("Órgão"),
        on_delete=PROTECT,
    )

    valor = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor (R$)"),
    )

    class Meta:
        verbose_name = _("Receita Orçamentária")
        verbose_name_plural = _("Receitas Orçamentárias")
        ordering = ["id"]
