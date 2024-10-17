import logging
import os

from django.conf import settings
from django.http.response import HttpResponse, Http404
from easy_thumbnails.files import get_thumbnailer
from image_cropping.utils import get_backend
from pymupdf import Point, Rect
from rest_framework.exceptions import NotFound
import fitz
import pymupdf

from cmj.core.models import AreaTrabalho
from sapl.utils import get_mime_type_from_file_extension


logger = logging.getLogger(__name__)


class ResponseFileMixin:

    def response_pagepdftoimage(self, arquivo, _page, _dpi, _grade='0'):

        _rect = None
        if _grade.isnumeric():
            _grade = int(_grade)
        else:
            _rect = Rect(*tuple(map(lambda x: int(x), _grade.split(','))))
            _grade = 25

        def grade_for_page(p, grade):
            w = int(p.rect.x1)
            h = int(p.rect.y1)

            if _rect:
                p.draw_rect(
                    _rect,
                    width=0,
                    fill=(0.5, 0, 0),
                    fill_opacity=0.5
                )

            for x in range(grade, w, grade):
                p.insert_text((x, 7), str(x), fontsize=7)
                p.draw_line(
                    (x, 0), (x, h),
                    color=(0.5, 0, 0),
                    width=0.5,
                    dashes="[3]",
                    stroke_opacity=0.5
                )
            for y in range(grade, h, grade):
                p.insert_text((1, y + 5), str(y), fontsize=7)
                p.draw_line(
                    (0, y), (w, y),
                    color=(0.5, 0, 0),
                    width=0.5,
                    dashes="[3]",
                    stroke_opacity=0.5  # , fill_opacity=1,
                )

        fcache_path = f'{arquivo.file}-p{_page:0>3}-d{_dpi:0>3}.png'
        if _grade < 10:
            if os.path.exists(fcache_path):
                with open(fcache_path, 'rb') as f:
                    response = HttpResponse(f, content_type='image/png')
                return response

        doc = fitz.open(arquivo.file)
        for index, page in enumerate(doc, 1):
            if index == _page:
                if _grade >= 10:
                    grade_for_page(page, _grade)
                png = page.get_pixmap(dpi=int(_dpi) if _dpi else 300)
                bpng = png.tobytes()

                if _grade < 10:
                    with open(fcache_path, 'wb') as f:
                        f.write(bpng)

                doc.close()
                response = HttpResponse(bpng, content_type='image/png')
                return response

        raise NotFound

    def anon(self, arquivo, page, grade, anon):
        """?page=1  # opcional, se colocado mostrará o resultado em png
            &dpi=150 # opcional, útil se usar page
            &grade=300,180,590,400, limita local na pagina a aplicar o anon.
            &anon=elemento1, elemento2, elemento3, ...
        """

        try:
            fin = arquivo.path
            doc = pymupdf.open(fin)
            pages = doc.pages() if not page else doc.pages(page - 1, page, 1)

            grade = tuple(filter(lambda y: y, map(
                lambda x: int(x), grade.split(','))))
            excludes = tuple(filter(lambda y: y, map(
                lambda x: x.strip(), anon.split(','))))

            for p in pages:
                r = Rect(*grade) if grade else p.rect
                areas_all = []

                for e in excludes:
                    areas = p.search_for(e)
                    areas_all.extend(areas)

                for area in areas_all:
                    if r.intersects(area):
                        p.add_redact_annot(
                            area, fill=(0, 0, 0))

                p.apply_redactions()

            if settings.DEBUG:
                doc.save('/home/leandro/TEMP/pdf_anon.pdf')
                doc.close()
                return
            fout = f'{fin}.new'
            doc.save(fout)
            doc.close()
            os.remove(fin)
            os.rename(fout, fin)

        except Exception as e:
            print(e)
            pass

    def response_file(self, request, *args, **kwargs):
        self.item = item = self.get_queryset().filter(pk = kwargs['pk']).first()
        page = request.GET.get('page', 0)
        dpi = request.GET.get('dpi', 72)
        grade = request.GET.get('grade', '0')
        anon = request.GET.get('anon', '')

        if not item:
            logger.info(f'response_file not item')
            raise NotFound

        if not hasattr(item, self.action):
            logger.info(f'response_file not attr action')
            raise NotFound

        arquivo = getattr(item, self.action)
        if not arquivo:
            logger.info(f'response_file not file')
            raise NotFound

        mime = get_mime_type_from_file_extension(arquivo.name)

        if request.user.is_superuser and anon and mime == 'application/pdf':
            self.anon(arquivo, int(page), grade, anon)

        if page and mime == 'application/pdf':
            return self.response_pagepdftoimage(arquivo, int(page), dpi, grade)

        if mime == 'application/png':
            mime = 'image/png'

        if mime == 'application/jpg':
            mime = 'image/jpg'

        custom_filename = arquivo.name.split('/')[-1]
        if hasattr(self, 'custom_filename'):
            custom_filename = self.custom_filename(item)

        thumbnail = self.thumbnail() if self.format_kwarg and mime.startswith('image') else None

        if settings.DEBUG:
            file_path = arquivo.original_path if 'original' in request.GET else arquivo.path

            if thumbnail:
                file_path = thumbnail.path

            with open(file_path, 'rb') as f:
                response = HttpResponse(f, content_type=mime)
            response['Content-Disposition'] = (
                'inline; filename="%s"' % custom_filename)
            return response

        response = HttpResponse(content_type='%s' % mime)
        response['Content-Disposition'] = (
            'inline; filename="%s"' % custom_filename)

        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0

        original = 'original__' if 'original' in request.GET else ''

        if thumbnail:
            original = ''
            arquivo = thumbnail.name

        response['X-Accel-Redirect'] = "/mediaredirect/{0}{1}".format(
            original,
            arquivo.name
        )

        logger.debug(f'response_file end method')
        return response

    def thumbnail(self):

        format = self.format_kwarg
        ext = format

        if '.' in format:
            format, ext = format.split('.')
        else:
            format = None

        arquivo = getattr(self.item, self.action)

        if not format:
            return arquivo

        if format[0] != 'c':
            thumbnail = get_thumbnailer(arquivo).get_thumbnail({
                    'size': (int(format), int(format)),
                    'box': None,
                    'crop': False,
                    'detail': True,
                }
            )
        else:
            size = format[1:]
            thumbnail = get_thumbnailer(arquivo).get_thumbnail({
                    'size': (int(size), int(size)),
                    'box': getattr(self.item, f'{self.action}_cropping'),
                    'crop': True,
                    'detail': True,
                }
            )
        return thumbnail


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
