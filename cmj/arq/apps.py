from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.arq'
    label = 'arq'
    verbose_name = _('Arq')

    def ready(self):
        from . import signals
