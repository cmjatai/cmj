from django.utils.text import slugify
from rest_framework.decorators import action

from sapl.api.mixins import ResponseFileMixin


class OficioAjusteLoaViewSet(ResponseFileMixin):

    def custom_filename(self, item):
        arcname = "{}-{}.{}".format(
            item.loa.ano, slugify(item.epigrafe), item.arquivo.path.split(".")[-1]
        )
        return arcname

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
