from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.loa'
    label = 'loa'
    verbose_name = _('Loa')