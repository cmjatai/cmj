from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.procuradoria'
    label = 'procuradoria'
    verbose_name = _('Procuradoria Geral')
