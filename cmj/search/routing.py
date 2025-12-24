
# timer_app/routing.py - Configuração de rotas WebSocket
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<session_id>[a-zA-Z0-9_-]+)/$', consumers.ChatConsumer.as_asgi()),
]
