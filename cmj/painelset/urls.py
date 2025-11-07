from django.urls.conf import re_path, include

# timer_app/urls.py - URLs da aplicação
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    re_path(
        r'^painelset',
        include(
            views.EventoCrud.get_urls() +
            views.IndividuoCrud.get_urls()
        )
    ),
    re_path(r'^painelset/painel',
        views.app_vue_painel, name='app_vue_painel_url'),

    re_path(r'^v2025',
        views.app_vue_v2025, name='app_vue_v2025_url'),
]
