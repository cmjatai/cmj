import logging
from django.apps.registry import apps
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.mixins import ResponseFileMixin
from django.db.models import Q
from rest_framework.decorators import action


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('loa')
    ]
)
