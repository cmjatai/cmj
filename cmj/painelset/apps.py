from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.painelset'
    label = 'painelset'
    verbose_name = _('Painel Set')

    def ready(self):
        from . import signals

