from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AppConfig(AppConfig):
    name = 'cmj.news'
    label = 'news'
    verbose_name = _('Notícias')
