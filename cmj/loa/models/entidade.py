from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.deletion import SET_NULL
from django.db.models.fields.json import JSONField
from django.utils.translation import gettext_lazy as _


class NaturezaJuridica(models.Model):

    codigo = models.CharField(
        max_length=4,
        verbose_name=_("Código"),
        validators=[RegexValidator(r"^\d{4}$", _("Código inválido"))],
    )

    descricao = models.CharField(
        max_length=256,
        verbose_name=_("Descrição"),
    )

    class Meta:
        verbose_name = _("Natureza Jurídica")
        verbose_name_plural = _("Naturezas Jurídicas")
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class TipoEntidade(models.Model):

    codigo = models.CharField(
        max_length=3,
        verbose_name=_("Código"),
        validators=[RegexValidator(r"^\d{3}$", _("Código inválido"))],
    )

    descricao = models.CharField(
        max_length=256,
        verbose_name=_("Descrição"),
    )

    SAUDE_CHOICE = 10
    EDUCACAO_CHOICE = 20
    ASSISTENCIA_SOCIAL_CHOICE = 30
    SEGURANCA_PUBLICA_CHOICE = 40
    CULTURA_CHOICE = 50
    ESPORTE_CHOICE = 60
    OUTROS_CHOICE = 70

    # tipo_geral é uma classificação mais ampla que agrupa vários tipos de entidade
    # será um choice com valores fixos definidos no código sendo: saúde, educação, assistência social, segurança pública, cultura, esporte, outros. criando através de números
    tipo_geral = models.PositiveSmallIntegerField(
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
        verbose_name = _("Tipo de Entidade")
        verbose_name_plural = _("Tipos de Entidades")
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class Entidade(models.Model):
    """Entidades públicas ou privadas que recebem recursos de emendas impositivas/modificativas."""

    nome_fantasia = models.CharField(
        max_length=256,
        verbose_name=_("Nome"),
    )

    razao_social = models.CharField(
        max_length=256,
        verbose_name=_("Nome Empresarial"),
    )

    cpfcnpj = models.CharField(
        max_length=18,
        blank=True,
        null=True,
        default=None,
        verbose_name=_("CNPJ"),
        # validators=[CNPJValidator()],
    )

    cnes = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        default=None,
        verbose_name=_("CNES"),
        validators=[RegexValidator(r"^\d{7}$", _("CNES inválido"))],
    )

    natureza_juridica = models.ForeignKey(
        "loa.NaturezaJuridica",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Natureza Jurídica"),
        on_delete=SET_NULL,
    )

    tipo_entidade = models.ForeignKey(
        "loa.TipoEntidade",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Tipo de Entidade"),
        on_delete=SET_NULL,
    )

    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    ativo = models.BooleanField(
        default=False,
        verbose_name=_("Ativo"),
    )

    class Meta:
        verbose_name = _("Entidade")
        verbose_name_plural = _("Entidades")
        ordering = ["nome_fantasia"]
        unique_together = (("cpfcnpj", "cnes"),)

    def __str__(self):
        nf = self.nome_fantasia
        tipo = self.tipo_entidade.descricao if self.tipo_entidade else ""
        return f'{nf}{" - CNES:" if self.cnes else (" - CNPJ:" if self.cpfcnpj else "")} {self.cnes or self.cpfcnpj or ""}'
