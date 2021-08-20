from django.contrib import admin
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from sapl.utils import register_all_models_in_admin

register_all_models_in_admin(__name__)

admin.site.site_title = 'Administração - SAPL'
admin.site.site_header = 'Administração - SAPL'
