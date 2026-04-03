from decimal import Decimal

from django.contrib.postgres.indexes import GinIndex, OpClass
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import CASCADE, PROTECT
from django.db.models.fields.json import JSONField
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from cmj.mixins import CmjSearchMixin
from cmj.utils import texto_upload_path
from sapl.parlamentares.models import Parlamentar
from sapl.utils import OverwriteStorage, PortalFileField


def ajuste_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath=instance.loa.ano)


class OficioAjusteLoa(models.Model):

    FIELDFILE_NAME = ("arquivo",)

    loa = models.ForeignKey(
        "loa.Loa",
        verbose_name=_("LOA"),
        related_name="ajusteloa_set",
        on_delete=PROTECT,
    )

    epigrafe = models.CharField(max_length=100, verbose_name=_("Epígrafe"))

    arquivo = PortalFileField(
        blank=True,
        null=True,
        upload_to=ajuste_upload_path,
        verbose_name=_("Ofício"),
        storage=OverwriteStorage(),
        max_length=512,
    )

    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=None,
        encoder=DjangoJSONEncoder,
    )

    parlamentares = models.ManyToManyField(
        Parlamentar,
        related_name="oficioajusteloa_set",
        verbose_name=_("Parlamentares"),
    )

    class Meta:
        verbose_name = _("Ofício de Ajuste Técnico")
        verbose_name_plural = _("Ofícios de Ajuste Técnico")
        ordering = ["id"]

    def __str__(self):
        ps = map(lambda x: x.nome_parlamentar, self.parlamentares.all())
        parlamentares = " / ".join(ps)
        return f"{self.epigrafe} - {parlamentares}"

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
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class RegistroAjusteLoa(CmjSearchMixin):

    SAUDE = 10
    DIVERSOS = 99
    TIPOEMENDALOA_CHOICE = ((SAUDE, _("Saúde")), (DIVERSOS, _("Áreas Diversas")))

    tipo = models.PositiveSmallIntegerField(
        choices=TIPOEMENDALOA_CHOICE, default=99, verbose_name=_("Área de aplicação")
    )

    oficio_ajuste_loa = models.ForeignKey(
        OficioAjusteLoa,
        verbose_name=_("Ofício de Ajuste Técnico"),
        related_name="registroajusteloa_set",
        on_delete=PROTECT,
    )

    emendaloa_old = models.ForeignKey(
        "loa.EmendaLoa",
        blank=True,
        null=True,
        default=None,
        verbose_name=_("Emenda Impositiva (old)"),
        related_name="registroajusteloa_old_set",
        db_column="emendaloa_id",
        on_delete=PROTECT,
    )

    emendaloa = models.ManyToManyField(
        "loa.EmendaLoa",
        blank=True,
        verbose_name=_("Emendas Impositivas"),
        related_name="registroajusteloa_set",
    )

    descricao = models.TextField(verbose_name=_("Descrição"))

    unidade = models.ForeignKey(
        "loa.UnidadeOrcamentaria",
        verbose_name=_("Unidade Orçamentária"),
        related_name="registroajusteloa_set",
        blank=True,
        null=True,
        default=None,
        on_delete=PROTECT,
    )

    entidade = models.ForeignKey(
        "loa.Entidade",
        verbose_name=_("Entidade"),
        related_name="registroajusteloa_set",
        blank=True,
        null=True,
        default=None,
        on_delete=PROTECT,
    )

    parlamentares_valor = models.ManyToManyField(
        "parlamentares.Parlamentar",
        through="RegistroAjusteLoaParlamentar",
        related_name="registroajusteloa_set",
        verbose_name=_("Parlamentares"),
        through_fields=("registro", "parlamentar"),
    )

    class Meta:
        verbose_name = _("Registro do Ajuste Técnico")
        verbose_name_plural = _("Registros do Ajuste Técnico")
        ordering = ["id"]

        indexes = [
            GinIndex(
                OpClass("search", name="gin_trgm_ops"),
                name="loa_rjl_search_gin_trgm",
            ),
        ]

    @property
    def fields_search(self):
        return [
            "hook_emendaloa__search",
            "descricao",
            "oficio_ajuste_loa",
            "entidade",
            "unidade",
        ]

    def hook_emendaloa__search(self):
        emendas = self.emendaloa.all()
        return " ".join(map(lambda x: x.search, emendas))

    @property
    def str_valor(self):
        soma = self.soma_valor
        str_v = formats.number_format(soma, force_grouping=True)
        if "-" in str_v:
            str_v = f"({str_v[1:]})"
        return str_v

    @property
    def soma_valor(self):
        if self.pk is None:
            return Decimal("0.00")
        soma = sum(
            list(
                filter(
                    lambda x: x,
                    self.registroajusteloaparlamentar_set.values_list(
                        "valor", flat=True
                    ),
                )
            )
        )
        return soma

    def __str__(self):
        return f"R$ {self.str_valor} - {self.oficio_ajuste_loa}"


class RegistroAjusteLoaParlamentar(models.Model):

    registro = models.ForeignKey(
        "loa.RegistroAjusteLoa",
        verbose_name=_("Registro de Ajuste"),
        related_name="registroajusteloaparlamentar_set",
        on_delete=CASCADE,
    )

    parlamentar = models.ForeignKey(
        "parlamentares.Parlamentar",
        related_name="registroajusteloaparlamentar_set",
        verbose_name=_("Parlamentar"),
        on_delete=PROTECT,
    )

    valor = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor por Parlamentar (R$)"),
    )

    def __str__(self):
        valor_str = formats.number_format(self.valor, force_grouping=True)
        return f"R$ {valor_str} - {self.parlamentar.nome_parlamentar}"

    class Meta:
        verbose_name = _("Participação Parlamentar no Registro de Ajuste Técnico")
        verbose_name_plural = _(
            "Participações Parlamentares no Registro de Ajuste Técnico"
        )
        ordering = ["id"]
