from django.db import models

from django.utils.translation import ugettext_lazy as _
import reversion
from sapl.utils import texto_upload_path, restringe_tipos_de_arquivo_txt


@reversion.register()
class TipoDeDiario(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Diário')
        verbose_name_plural = _('Tipos de Diário')


def diario_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath=instance.ano)


@reversion.register()
class DiarioOficial(models.Model):

    edicao = models.PositiveIntegerField(
        default=0,
        verbose_name='Edição')

    descricao = models.CharField(max_length=250, verbose_name=_('Descrição'))

    tipo = models.ForeignKey(
        TipoDeDiario,
        on_delete=models.PROTECT,
        verbose_name=_('Tipo do Diário'))

    data = models.DateField(
        blank=True, null=True, verbose_name=_('Data'))

    arquivo = models.FileField(
        blank=True,
        null=True,
        upload_to=diario_upload_path,
        verbose_name=_('Arquivo Digital do Diário'),
        validators=[restringe_tipos_de_arquivo_txt])

    class Meta:
        verbose_name = _('Diário Oficial')
        verbose_name_plural = _('Diários Oficiais')