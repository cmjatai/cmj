from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.sigad'
    label = 'sigad'
    verbose_name = _('Sistema Informatizado '
                     'de Gestão Arquivística de Documentos')

    def ready(self):
        from . import signals