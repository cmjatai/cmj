
from django import apps
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.search'
    label = 'search'
    verbose_name = _('Busca Textual')
