from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.cerimonial'
    label = 'cerimonial'
    verbose_name = _('Cerimonial')