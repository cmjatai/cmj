from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.api'
    label = 'cmj_api'
    verbose_name = _('API Rest')
