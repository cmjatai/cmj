from django.db import models
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page


# Create your models here.
class HomePage(Page):
    descricao = models.CharField(_('Descrição'), max_length=250)

    content_panels = Page.content_panels + [
        FieldPanel('descricao', classname="full")
    ]

    class Meta:
        verbose_name = _('Página..')
        verbose_name_plural = _('Páginas')
