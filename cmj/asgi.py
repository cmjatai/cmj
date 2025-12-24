"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os

from django.conf import settings
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import django
from django.core.handlers.asgi import ASGIHandler

import cmj.core.routing
import cmj.painelset.routing
import cmj.search.routing


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmj.settings")

django.setup()

http_handler = ASGIHandler()
if settings.DEBUG:
    http_handler = ASGIStaticFilesHandler(http_handler)

application = ProtocolTypeRouter({
    'http': http_handler,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            cmj.core.routing.websocket_urlpatterns +
            cmj.painelset.routing.websocket_urlpatterns +
            cmj.search.routing.websocket_urlpatterns
        )
    ),
    # Just HTTP for now. (We can add other protocols later.)
})
