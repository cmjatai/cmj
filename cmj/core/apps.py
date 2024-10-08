
from django import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.core'
    label = 'core'
    verbose_name = _('Ajuste Principais')

    def ready(self):
        from . import signals
