
from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.compilacao'
    label = 'compilacao'
    verbose_name = _('Compilação')

    def ready(self):
        apps.AppConfig.ready(self)

        from . import signals
