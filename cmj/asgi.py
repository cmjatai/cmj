"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import django
from django.core.handlers.asgi import ASGIHandler

import cmj.core.routing


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmj.settings")

django.setup()

application = ProtocolTypeRouter({
    'http': ASGIHandler(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            cmj.core.routing.websocket_urlpatterns
        )
    ),
    # Just HTTP for now. (We can add other protocols later.)
})
