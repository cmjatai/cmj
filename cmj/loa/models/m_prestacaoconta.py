from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT
from django.db.models.fields.json import JSONField
from django.utils.translation import gettext_lazy as _

from cmj.utils import texto_upload_path
from sapl.utils import PortalFileField


def prestacaoconta_upload_path(instance, filename):
    return texto_upload_path(
        instance, filename, subpath=instance.prestacao_conta.loa.ano
    )


def prestacaocontaregistro_upload_path(instance, filename):
    return texto_upload_path(
        instance, filename, subpath=instance.registro.prestacao_conta.loa.ano
    )


class PrestacaoContaLoa(models.Model):

    loa = models.ForeignKey(
        "loa.Loa",
        verbose_name=_("LOA"),
        related_name="prestacaoconta_set",
        on_delete=PROTECT,
    )

    data_envio = models.DateField(
        verbose_name=_("Data de Envio"), blank=True, null=True, default=None
    )

    epigrafe = models.CharField(max_length=100, verbose_name=_("Epígrafe"))

    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=None,
        encoder=DjangoJSONEncoder,
    )

    class Meta:
        verbose_name = _("Prestação de Contas das Emendas Impositivas")
        verbose_name_plural = _("Prestações de Contas das Emendas Impositivas")
        ordering = ["id"]

    def __str__(self):
        return f"{self.epigrafe} - {self.loa.ano}"


class ArquivoPrestacaoContaLoa(models.Model):

    FIELDFILE_NAME = ("arquivo",)

    prestacao_conta = models.ForeignKey(
        "loa.PrestacaoContaLoa",
        verbose_name=_("Prestação de Conta LOA"),
        related_name="arquivoprestacaocontaloa_set",
        on_delete=PROTECT,
    )

    arquivo = PortalFileField(
        blank=True,
        null=True,
        upload_to=prestacaoconta_upload_path,
        verbose_name=_("Arquivo Anexo"),
        max_length=512,
    )

    descricao = models.CharField(
        max_length=256, verbose_name=_("Descrição"), default="", blank=True
    )

    class Meta:
        verbose_name = _("Arquivo da Prestação de Conta LOA")
        verbose_name_plural = _("Arquivos da Prestação de Conta LOA")
        ordering = ["id"]

    def __str__(self):
        return f"{self.descricao} - {self.prestacao_conta.loa.ano}"

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):

        if not self.pk and self.arquivo:
            arquivo = self.arquivo
            self.arquivo = None
            models.Model.save(
                self,
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields,
            )
            self.arquivo = arquivo
            update_fields = ("arquivo",)

        return models.Model.save(
            self,
            force_insert=False,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class PrestacaoContaRegistro(models.Model):

    class SituacaoChoices(models.TextChoices):
        EM_EXECUCAO = "EM_EXECUCAO", _("Em Execução")
        FINALIZADO = "FINALIZADO", _("Finalizada")

    prestacao_conta = models.ForeignKey(
        "loa.PrestacaoContaLoa",
        verbose_name=_("Prestação de Conta LOA"),
        related_name="prestacaocontaregistro_set",
        on_delete=PROTECT,
    )

    registro_ajuste = models.ForeignKey(
        "loa.RegistroAjusteLoa",
        verbose_name=_("Registro de Ajuste Técnico"),
        related_name="prestacaocontaregistro_set",
        on_delete=PROTECT,
        blank=True,
        null=True,
        default=None,
    )

    emendaloa = models.ForeignKey(
        "loa.EmendaLoa",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Emenda Impositiva"),
        related_name="prestacaocontaregistro_set",
        on_delete=PROTECT,
    )

    detalhamento = models.TextField(
        verbose_name=_("Detalhamento"), blank=True, null=True, default=""
    )

    situacao = models.CharField(
        choices=SituacaoChoices.choices,
        max_length=20,
        default=SituacaoChoices.EM_EXECUCAO,
        verbose_name=_("Situação"),
    )

    class Meta:
        verbose_name = _("Registro de Prestação de Conta")
        verbose_name_plural = _("Registros de Prestação de Conta")
        ordering = ["prestacao_conta__data_envio", "id"]

    def __str__(self):
        return (
            f"{self.prestacao_conta.loa.ano} - {self.registro_ajuste or self.emendaloa}"
        )


class ArquivoPrestacaoContaRegistro(models.Model):

    FIELDFILE_NAME = ("arquivo",)

    registro = models.ForeignKey(
        "loa.PrestacaoContaRegistro",
        verbose_name=_("Registro de Prestação de Conta"),
        related_name="arquivoprestacaocontaregistro_set",
        on_delete=PROTECT,
    )

    arquivo = PortalFileField(
        blank=True,
        null=True,
        upload_to=prestacaocontaregistro_upload_path,
        verbose_name=_("Arquivo Anexo"),
        max_length=512,
    )

    descricao = models.CharField(
        max_length=256, verbose_name=_("Descrição"), default="", blank=True
    )

    class Meta:
        verbose_name = _("Arquivo do Registro de Prestação de Conta")
        verbose_name_plural = _("Arquivos do Registro de Prestação de Conta")
        ordering = ["id"]

    def __str__(self):
        return f"{self.descricao} - {self.registro.prestacao_conta.loa.ano}"

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):

        if not self.pk and self.arquivo:
            arquivo = self.arquivo
            self.arquivo = None
            models.Model.save(
                self,
                force_insert=force_insert,
                force_update=force_update,
                using=using,
                update_fields=update_fields,
            )
            self.arquivo = arquivo
            update_fields = ("arquivo",)

        return models.Model.save(
            self,
            force_insert=False,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
