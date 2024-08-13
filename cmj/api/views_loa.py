import logging

from django.apps.registry import apps
from django.db.models import Q
from django.utils.text import slugify
from rest_framework.decorators import action

from cmj.loa.models import OficioAjusteLoa
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.mixins import ResponseFileMixin


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('loa')
    ]
)


@customize(OficioAjusteLoa)
class _OficioAjusteLoaViewSet(ResponseFileMixin):

    def custom_filename(self, item):
        arcname = '{}-{}.{}'.format(
            item.loa.ano,
            slugify(item.epigrafe),
            item.arquivo.path.split('.')[-1])
        return arcname

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
