import logging

from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http.response import Http404
from rest_framework.decorators import action
from rest_framework.response import Response

from cmj.cerimonial.models import Visitante, Visita
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.mixins import ResponseFileMixin


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        # apps.get_app_config('cerimonial')
        Visitante,
        Visita
    ]
)


@customize(Visita)
class _Visita(ResponseFileMixin):

    @action(detail=True)
    def fotografia(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)


@customize(Visitante)
class _Visitante(ResponseFileMixin):

    @action(detail=True)
    def fotografia(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
