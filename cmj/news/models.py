from django.db import models
from sapl.parlamentares.models import Parlamentar
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page


class NewsPage(Page):
    descricao = models.CharField(_('Descrição'), max_length=250)

    texto = RichTextField(blank=True)

    parlamentares = models.ManyToManyField(
        Parlamentar,
        blank=True,
        verbose_name=_('Notícia de Parlamentares'))

    content_panels = Page.content_panels + [
        FieldPanel('descricao', classname="full")
    ]

    class Meta:
        verbose_name = _('Página..')
        verbose_name_plural = _('Páginas')
