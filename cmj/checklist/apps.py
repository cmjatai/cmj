from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = "cmj.checklist"
    label = "checklist"
    verbose_name = _("Checklist")
