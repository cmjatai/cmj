from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.home'
    label = 'home'
    verbose_name = _('Página Inicial')