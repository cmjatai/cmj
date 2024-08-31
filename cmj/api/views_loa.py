import logging

from django.apps.registry import apps
from django.conf import settings
from django.db.models import Q
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.utils.text import slugify
import pymupdf
from rest_framework.decorators import action

from cmj.loa.models import OficioAjusteLoa, EmendaLoa
from cmj.settings.medias import MEDIA_URL
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.mixins import ResponseFileMixin
from sapl.base.models import CasaLegislativa
from sapl.relatorios.views import make_pdf


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


@customize(EmendaLoa)
class _EmendaLoaViewSet:

    @action(detail=True)
    def preview(self, request, *args, **kwargs):
        #base_url = settings.MEDIA_ROOT if settings.DEBUG else request.build_absolute_uri()
        base_url = request.build_absolute_uri()

        el = self.get_object()

        context = {
            'object': el
        }

        template = render_to_string('loa/pdf/emendaloa_preview.html', context)
        pdf_file = make_pdf(base_url=base_url, main_template=template)
        doc = pymupdf.Document(stream=pdf_file)

        try:
            p = int(request.GET.get('page', 0))
        except:
            p = 0

        d2b = doc
        if p:
            p -= 1
            page = doc[p % len(doc)]
            d2b = page.get_pixmap(dpi=300)

        bresponse = d2b.tobytes()
        doc.close()

        response = HttpResponse(
            bresponse, content_type='image/png' if p else 'application/pdf')
        return response
