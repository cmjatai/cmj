from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.diarios'
    label = 'diarios'
    verbose_name = _('Diários Oficiais')