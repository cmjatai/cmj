from django import apps
from django.utils.translation import ugettext_lazy as _


class AppConfig(apps.AppConfig):
    name = 'cmj.s3_to_cmj'
    label = 's3_to_cmj'
    verbose_name = _('S3 Import Sapl 3.0 de Jataí')
