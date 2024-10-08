import logging

from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http.response import Http404
from django.utils.text import slugify
from rest_framework.decorators import action
from rest_framework.response import Response

from cmj.api.serializers import BiSerializer
from cmj.core.models import Bi, CertidaoPublicacao
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.mixins import ResponseFileMixin

logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('core')
    ]
)


@customize(Bi)
class _BiViewSet:
    serializer_class = BiSerializer


@customize(CertidaoPublicacao)
class _CertidaoPublicacaoViewSet(ResponseFileMixin):

    def custom_filename__(self, item):
        arcname = '{}-{}.{}'.format(
            item.loa.ano,
            slugify(item.epigrafe),
            item.arquivo.path.split('.')[-1])
        return arcname

    @action(detail = True)
    def certificado(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
