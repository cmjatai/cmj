from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cmj3.core'
    label = 'core'
    verbose_name = _('Núcleo')
