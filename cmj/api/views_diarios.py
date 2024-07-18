import logging

from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http.response import Http404
from django.utils.text import slugify
from rest_framework.decorators import action
from rest_framework.response import Response

from cmj.diarios.models import DiarioOficial
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.mixins import ResponseFileMixin


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('diarios')
    ]
)


@customize(DiarioOficial)
class _DiarioOficialViewSet(ResponseFileMixin):

    def custom_filename(self, item):
        arcname = '{}-{:03d}-{}.{}'.format(
            item.data.year,
            item.edicao,
            slugify(item.tipo.descricao),
            item.arquivo.path.split('.')[-1])
        return arcname

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
