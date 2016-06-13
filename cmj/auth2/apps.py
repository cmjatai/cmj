from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.auth2'
    label = 'auth2'
    verbose_name = _('Autenticação de Usuário')