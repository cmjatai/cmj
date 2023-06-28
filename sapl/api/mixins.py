from django.conf import settings
from django.http.response import HttpResponse
import fitz
from rest_framework.exceptions import NotFound

from cmj.core.models import AreaTrabalho
from sapl.utils import get_mime_type_from_file_extension


class ResponseFileMixin:

    def response_pagepdftoimage(self, arquivo, _page, _dpi):
        doc = fitz.open(arquivo.file)

        for index, page in enumerate(doc, 1):
            if index == _page:
                png = page.get_pixmap(dpi=int(_dpi) if _dpi else 300)
                bpng = png.tobytes()
                response = HttpResponse(bpng, content_type='image/png')
                return response

    def response_file(self, request, *args, **kwargs):
        item = self.get_queryset().filter(pk=kwargs['pk']).first()
        page = request.GET.get('page', None)
        dpi = request.GET.get('dpi', None)

        if not item:
            raise NotFound

        if not hasattr(item, self.action):
            raise NotFound

        arquivo = getattr(item, self.action)
        if not arquivo:
            raise NotFound

        mime = get_mime_type_from_file_extension(arquivo.name)

        if page and mime == 'application/pdf':
            return self.response_pagepdftoimage(arquivo, int(page), dpi)

        if mime == 'application/png':
            mime = 'image/png'

        if settings.DEBUG:
            file_path = arquivo.original_path if 'original' in request.GET else arquivo.path

            with open(file_path, 'rb') as f:
                response = HttpResponse(f, content_type=mime)
            return response

        custom_filename = arquivo.name.split('/')[-1]
        if hasattr(self, 'custom_filename'):
            custom_filename = self.custom_filename(item)

        response = HttpResponse(content_type='%s' % mime)
        response['Content-Disposition'] = (
            'inline; filename="%s"' % custom_filename)

        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0

        original = 'original__' if 'original' in request.GET else ''

        response['X-Accel-Redirect'] = "/media/{0}{1}".format(
            original,
            arquivo.name
        )

        return response


class ControlAccessFileForContainerMixin(ResponseFileMixin):

    def get_queryset(self):
        qs = super().get_queryset()

        u = self.request.user

        param_tip_pub = {
            '%s__tipo' % '__'.join(self.container_field.split('__')[:-1]):
            AreaTrabalho.TIPO_PUBLICO
        }

        param_user = {
            self.container_field: u
        }

        if u.is_anonymous or not u.areatrabalho_set.exists():
            qs = qs.filter(**param_tip_pub)
        else:
            if u.has_perms(self.permission_required):
                qs = qs.filter(**param_user)
            else:
                qs = qs.filter(**param_tip_pub)

        return qs
