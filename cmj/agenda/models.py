from django.db import models
from django.db.models.deletion import SET_NULL, PROTECT, CASCADE
from django.db.models.fields.related import ManyToManyField
from django.utils.translation import ugettext_lazy as _
from sapl.base.models import Autor
from sapl.parlamentares.models import Partido, Parlamentar

from cmj.core.models import AreaTrabalho


class Evento(models.Model):
    inicio = models.DateTimeField(_("Início"))
    fim = models.DateTimeField(_("Fim"))
    titulo = models.CharField(_("Título"), max_length=255)
    descricao = models.TextField(_("Descrição"))

    workspace = models.ForeignKey(
        AreaTrabalho,
        verbose_name=_('Área de Trabalho'),
        related_name='evento_set', on_delete=PROTECT)

    solicitante = models.CharField(_("Solicitante"),
                                   blank=True, max_length=255)

    class Meta:
        verbose_name = _('Evento')
        verbose_name_plural = _('Eventos')


class Programacao(models.Model):
    inicio = models.DateTimeField(_("Início"))
    fim = models.DateTimeField(_("Fim"))

    titulo = models.CharField(_("Título"), max_length=255)
    descricao = models.TextField(_("Descrição"))

    evento = models.ForeignKey(
        Evento,
        verbose_name=_('Programacao do Evento'),
        related_name='programacao_set', on_delete=CASCADE)
