import logging

from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http.response import Http404
from rest_framework.decorators import action
from rest_framework.response import Response

from cmj.api.serializers import BiSerializer
from cmj.core.models import Bi
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('core')
    ]
)


@customize(Bi)
class _BiViewSet:
    serializer_class = BiSerializer
