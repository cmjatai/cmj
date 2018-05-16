from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.agenda'
    label = 'agenda'
    verbose_name = _('Agenda')

    def ready(self):
        from . import signals