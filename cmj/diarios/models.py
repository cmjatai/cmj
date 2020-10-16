from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.fields import related_descriptors
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
import reversion

from cmj.mixins import CommonMixin, CmjCleanMixin
from cmj.utils import texto_upload_path
from sapl.utils import restringe_tipos_de_arquivo_txt, OverwriteStorage


@reversion.register()
class TipoDeDiario(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))
    principal = models.BooleanField(default=False, verbose_name=_('Principal'))

    class Meta:
        verbose_name = _('Tipo de Diário')
        verbose_name_plural = _('Tipos de Diário')

    def __str__(self):
        return self.descricao


def diario_upload_path(instance, filename):
    return texto_upload_path(instance, filename, subpath=instance.ano)


@reversion.register()
class DiarioOficial(CommonMixin):
    FIELDFILE_NAME = ('arquivo', )

    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=None, encoder=DjangoJSONEncoder)

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
        storage=OverwriteStorage(),
        verbose_name=_('Arquivo Digital do Diário'),
        validators=[restringe_tipos_de_arquivo_txt])

    normas = models.ManyToManyField(
        'norma.NormaJuridica',
        verbose_name=_('Normas Publicadas no Diário'))

    data_ultima_atualizacao = models.DateTimeField(
        blank=True, null=True,
        auto_now=True,
        verbose_name=_('Data'))

    class Meta:
        verbose_name = _('Diário Oficial')
        verbose_name_plural = _('Diários Oficiais')
        ordering = ('-data', 'edicao')

    def __str__(self):
        return self.descricao

    @property
    def ano(self):
        return self.data.year

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if not self.pk and self.arquivo:
            arquivo = self.arquivo
            self.arquivo = None
            models.Model.save(self, force_insert=force_insert,
                              force_update=force_update,
                              using=using,
                              update_fields=update_fields)
            self.arquivo = arquivo

        return models.Model.save(self, force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields)


class VinculoDocDiarioOficial(CmjCleanMixin, models.Model):

    diario = models.ForeignKey(
        DiarioOficial,
        on_delete=models.PROTECT,
        verbose_name=_('Diário Oficial'))

    pagina = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Página Inicial'))

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None,
        on_delete=models.PROTECT,
        verbose_name=_('Espécie'))
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )

    class Meta:
        verbose_name = _('Documento Publicado no Diário Oficial')
        verbose_name_plural = _('Documentos Publicados no Diário Oficial')
        ordering = ('id', )
        unique_together = (('object_id', 'content_type', 'diario'), )

    def __str__(self):
        return str(self.content_object)

    @property
    def reverse_link_content_object(self):
        return reverse(f'{self.content_object._meta.app_config.name}:{self.content_object._meta.model_name}_detail', kwargs={'pk': self.content_object.id})
