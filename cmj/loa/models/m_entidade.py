from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.deletion import SET_NULL
from django.db.models.fields.json import JSONField
from django.utils.translation import gettext_lazy as _

from cmj.mixins import CmjAuditoriaModelMixin


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


class DocumentoHabilitacao(models.Model):
    """Lista de Documentos para Habilitação de entidades."""

    titulo = models.CharField(
        max_length=256,
        verbose_name=_("Documento"),
    )

    descricao = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Descrição"),
    )

    # nível de obrigatoriedade do documento, sendo: 1 - obrigatório, 2 - opcional, 3 - facultativo
    OBRIGATORIO_CHOICE = 1
    OPCIONAL_CHOICE = 2
    FACULTATIVO_CHOICE = 3

    nivel_obrigatoriedade = models.PositiveSmallIntegerField(
        choices=(
            (OBRIGATORIO_CHOICE, _("Obrigatório")),
            (OPCIONAL_CHOICE, _("Opcional")),
            (FACULTATIVO_CHOICE, _("Facultativo")),
        ),
        default=OPCIONAL_CHOICE,
        verbose_name=_("Nível de Obrigatoriedade"),
    )

    class Meta:
        verbose_name = _("Documento de Habilitação")
        verbose_name_plural = _("Documentos de Habilitação")
        ordering = ["titulo"]

    def __str__(self):
        nivel_dict = {
            self.OBRIGATORIO_CHOICE: _("Obrigatório"),
            self.OPCIONAL_CHOICE: _("Opcional"),
            self.FACULTATIVO_CHOICE: _("Facultativo"),
        }
        return f"{nivel_dict.get(self.nivel_obrigatoriedade, '')} - {self.titulo}"


class EntidadeLoa(models.Model):
    """Relacionamento entre LOA e Entidade."""

    loa = models.ForeignKey(
        "loa.Loa",
        on_delete=models.CASCADE,
        verbose_name=_("LOA"),
    )

    entidade = models.ForeignKey(
        "loa.Entidade",
        on_delete=models.CASCADE,
        verbose_name=_("Entidade"),
    )

    class Meta:
        verbose_name = _("Entidade da LOA")
        verbose_name_plural = _("Entidades da LOA")
        unique_together = (("loa", "entidade"),)

    def __str__(self):
        return f"{self.loa} - {self.entidade}"

class DocHabEntidadeLoa(CmjAuditoriaModelMixin):
    """Relacionamento entre Loa, Entidade e seus Documentos de Habilitação."""

    entidade_loa = models.ForeignKey(
        "loa.EntidadeLoa",
        on_delete=models.CASCADE,
        verbose_name=_("Entidade LOA"),
    )

    documento_habilitacao = models.ForeignKey(
        "loa.DocumentoHabilitacao",
        on_delete=models.CASCADE,
        verbose_name=_("Documento Habilitação"),
    )

    validado = models.BooleanField(
        default=False,
        verbose_name=_("Validado"),
    )

    class Meta:
        verbose_name = _("Documento de Habilitação da Entidade")
        verbose_name_plural = _("Documentos de Habilitação das Entidades")
        unique_together = (("entidade_loa", "documento_habilitacao"),)

    def __str__(self):
        return f"{self.entidade_loa} - {self.documento_habilitacao}"


class DocHabEntidadeLoaArquivo(models.Model):
    """Arquivos enviados pelas entidades para comprovação de documentos de habilitação."""

    doc_hab_entidade_loa = models.ForeignKey(
        "loa.DocHabEntidadeLoa",
        on_delete=models.CASCADE,
        verbose_name=_("Documento Habilitação Entidade LOA"),
    )

    arquivo = models.FileField(
        upload_to="documentos_habilitacao/",
        verbose_name=_("Arquivo"),
    )

    class Meta:
        verbose_name = _("Arquivo de Documento de Habilitação da Entidade")
        verbose_name_plural = _("Arquivos de Documentos de Habilitação das Entidades")

    def __str__(self):
        return f"{self.doc_hab_entidade_loa} - {self.arquivo.name}"
