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
    )
]
