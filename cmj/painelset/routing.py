
# timer_app/routing.py - Configuração de rotas WebSocket
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # re_path(r'^ws/cronometro/$', consumers.CronometroConsumer.as_asgi()),
    re_path(r'ws/cronometro/(?P<timer_id>[0-9]+)/$', consumers.CronometroConsumer.as_asgi()),
]
