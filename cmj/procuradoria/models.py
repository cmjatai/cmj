from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
import reversion

from cmj.utils import RANGE_ANOS, texto_upload_path
from sapl.utils import OverwriteStorage


@reversion.register()
class TipoDocumentoProcuradoria(models.Model):
    sigla = models.CharField(max_length=5, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Documento da Procuradoria')
        verbose_name_plural = _('Tipos de Documentos da Procuradoria')
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


@reversion.register()
class DocumentoProcuradoria(models.Model):
    tipo = models.ForeignKey(
        TipoDocumentoProcuradoria, on_delete=models.PROTECT,
        verbose_name=_('Tipo Documento'))

    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'),
                                           choices=RANGE_ANOS)

    data = models.DateField(verbose_name=_('Data'))

    interessado = models.CharField(
        max_length=50, blank=True, verbose_name=_('Interessado'))

    ementa = models.TextField(verbose_name=_('Ementa'))

    observacao = models.TextField(
        blank=True, verbose_name=_('Observação'))
    resumo = models.TextField(
        blank=True, verbose_name=_('Resumo'))

    texto_integral = models.FileField(
        blank=True,
        null=True,
        storage=OverwriteStorage(),
        upload_to=texto_upload_path,
        verbose_name=_('Texto Integral'))

    class Meta:
        verbose_name = _('Documento da Procuradoria')
        verbose_name_plural = _('Documentos da Procuradoria')

    def __str__(self):
        return _('%(tipo)s - %(ementa)s') % {
            'tipo': self.tipo, 'ementa': self.ementa
        }

    def delete(self, using=None, keep_parents=False):
        if self.texto_integral:
            self.texto_integral.delete()

        return models.Model.delete(
            self, using=using, keep_parents=keep_parents)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.texto_integral:
            texto_integral = self.texto_integral
            self.texto_integral = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.texto_integral = texto_integral

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)
