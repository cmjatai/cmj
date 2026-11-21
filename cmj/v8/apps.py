from django import apps
from django.utils.translation import gettext_lazy as _


class AppConfig(apps.AppConfig):
    name = "cmj.v8"
    label = "v8"
    verbose_name = _("Frontend v8")
