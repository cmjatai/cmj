from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.ouvidoria'
    label = 'ouvidoria'
    verbose_name = _('Ouvidoria')

    def ready(self):
        from . import signals