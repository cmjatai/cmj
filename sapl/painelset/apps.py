from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'sapl.painelset'
    label = 'painelset'
    verbose_name = _('Painel Eletrônico')
