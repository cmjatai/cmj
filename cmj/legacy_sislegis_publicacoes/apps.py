from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.legacy_sislegis_publicacoes'
    label = 'legacy_sislegis_publicacoes'
    verbose_name = _('Import Sislegis Publicações')
