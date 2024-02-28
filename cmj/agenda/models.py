from django.db import models
from django.db.models.deletion import SET_NULL, PROTECT, CASCADE
from django.db.models.fields.related import ManyToManyField
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from sapl.base.models import Autor
from sapl.parlamentares.models import Partido, Parlamentar

from cmj.core.models import AreaTrabalho


class TipoEvento(models.Model):
    titulo = models.CharField(_("Título"), max_length=255)
    descricao = models.TextField(_("Descrição"))

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _('Tipo de Evento')
        verbose_name_plural = _('Tipos de Eventos')
        ordering = ['id']


class Evento(models.Model):

    EVENTO = 0
    FERIADO = 1
    CARACTERISTICA_CHOICE = ((EVENTO, _('Eventos Diversos')),
                             (FERIADO, _('Feriado')))

    inicio = models.DateTimeField(_("Início"))
    fim = models.DateTimeField(_("Fim"), blank=True, null=True)
    titulo = models.CharField(_("Título"), max_length=255)
    descricao = models.TextField(_("Descrição"))

    tipo = models.ForeignKey(
        TipoEvento,
        verbose_name=_('Tipo de Evento'),
        related_name='+', on_delete=PROTECT)

    caracteristica = models.PositiveSmallIntegerField(
        choices=CARACTERISTICA_CHOICE,
        default=0, verbose_name=_('Caracteristica?'))

    link_externo = models.URLField(_('Url Externa'), default='', blank=True)

    workspace = models.ForeignKey(
        AreaTrabalho,
        verbose_name=_('Área de Trabalho'),
        related_name='evento_set', on_delete=PROTECT)

    solicitante = models.CharField(_("Solicitante"),
                                   blank=True, max_length=255)

    class Meta:
        ordering = ('-inicio', )
        verbose_name = _('Evento')
        verbose_name_plural = _('Eventos')

    def __str__(self):
        return '{} - {}'.format(
            formats.date_format(self.inicio, 'd/m/Y - H:i'),
            self.titulo)


class Programacao(models.Model):
    inicio = models.DateTimeField(_("Início"))
    fim = models.DateTimeField(_("Fim"))

    titulo = models.CharField(_("Título"), max_length=255)
    descricao = models.TextField(_("Descrição"))

    evento = models.ForeignKey(
        Evento,
        verbose_name=_('Programacao do Evento'),
        related_name='programacao_set', on_delete=CASCADE)

    class Meta:
        ordering = ['id']
