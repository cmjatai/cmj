from django.urls.conf import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/time-refresh/$', consumers.TimeRefreshConsumer.as_asgi()),
]
