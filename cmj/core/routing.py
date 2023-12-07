from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^ws/time-refresh/$', consumers.TimeRefreshConsumer.as_asgi()),
]
