from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.painel'
    label = 'painel'
    verbose_name = _('Painel Eletrônico')
