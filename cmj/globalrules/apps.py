from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.globalrules'
    label = 'globalrules'
    verbose_name = _('Regras e Permissões para o Portal')
