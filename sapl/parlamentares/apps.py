from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.parlamentares'
    label = 'parlamentares'
    verbose_name = _('Parlamentares')
