import logging

from django.apps.registry import apps

from drfautoapi.drfautoapi import ApiViewSetConstrutor

logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('videos')
    ]
)
