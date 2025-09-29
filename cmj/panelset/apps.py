from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.panelset'
    label = 'panelset'
    verbose_name = _('Panel Set')

    def ready(self):
        from . import signals
