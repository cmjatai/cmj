
# timer_app/routing.py - Configuração de rotas WebSocket
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/timer/(?P<timer_id>[0-9a-f-]+)/$', consumers.CronometroConsumer.as_asgi()),
]
