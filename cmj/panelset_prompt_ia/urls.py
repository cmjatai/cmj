from django.urls.conf import re_path, include

# timer_app/urls.py - URLs da aplicação
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from .apps import AppConfig

app_name = AppConfig.name


router = DefaultRouter()
router.register(r'timers', views.TimerViewSet)

urlpatterns = [
    # API REST
    path('api/', include(router.urls)),

    # Endpoints específicos para operações de cronômetro
    path('api/timers/<uuid:timer_id>/start/', views.start_timer, name='start_timer'),
    path('api/timers/<uuid:timer_id>/pause/', views.pause_timer, name='pause_timer'),
    path('api/timers/<uuid:timer_id>/resume/', views.resume_timer, name='resume_timer'),
    path('api/timers/<uuid:timer_id>/stop/', views.stop_timer, name='stop_timer'),

    # Endpoint para árvore de cronômetros
    path('api/timers/<uuid:timer_id>/tree/', views.timer_tree, name='timer_tree'),

    # Interface web
    path('painelset/', views.timer_dashboard, name='dashboard'),
    path('painelset/timer/<uuid:timer_id>/', views.timer_detail, name='timer_detail'),
]
