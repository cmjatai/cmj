from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.protocoloadm'
    label = 'protocoloadm'
    verbose_name = _('Protocolo Administrativo')

    def ready(self):
        from . import signals
