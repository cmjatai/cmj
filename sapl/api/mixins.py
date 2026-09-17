import io
import logging
import os

import fitz
import pymupdf
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse
from easy_thumbnails.files import get_thumbnailer
from PIL import Image, ImageDraw
from pymupdf import Rect
from rest_framework.exceptions import NotFound

from cmj.core.models import AreaTrabalho
from cmj.utils import clean_text
from sapl.utils import get_mime_type_from_file_extension

logger = logging.getLogger(__name__)


class ResponseFileMixin:

    def response_pagepdftoimage(self, arquivo, _page, _dpi, _grade="0"):

        nocache = self.request.GET.get("nocache", False)

        _rect = None
        if _grade.isnumeric():
            _grade = int(_grade)
        else:
            _rect = Rect(*tuple(map(lambda x: int(x), _grade.split(","))))
            _grade = 25

        def grade_for_page(p, grade):
            w = int(p.rect.x1)
            h = int(p.rect.y1)

            if _rect:
                p.draw_rect(_rect, width=0, fill=(0.5, 0, 0), fill_opacity=0.5)

            for x in range(grade, w, grade):
                p.insert_text((x, 7), str(x), fontsize=7)
                p.draw_line(
                    (x, 0),
                    (x, h),
                    color=(0.5, 0, 0),
                    width=0.5,
                    dashes="[3]",
                    stroke_opacity=0.5,
                )
            for y in range(grade, h, grade):
                p.insert_text((1, y + 5), str(y), fontsize=7)
                p.draw_line(
                    (0, y),
                    (w, y),
                    color=(0.5, 0, 0),
                    width=0.5,
                    dashes="[3]",
                    stroke_opacity=0.5,  # , fill_opacity=1,
                )

        fcache_path = f"{arquivo.file}-p{_page:0>3}-d{_dpi:0>3}.png"
        if _grade < 10:
            if not nocache and os.path.exists(fcache_path):
                with open(fcache_path, "rb") as f:
                    response = HttpResponse(f, content_type="image/png")
                return response
            elif os.path.exists(fcache_path):
                os.remove(fcache_path)

        doc = fitz.open(arquivo.file)
        for index, page in enumerate(doc, 1):
            if index == _page:
                if _grade >= 10:
                    grade_for_page(page, _grade)
                png = page.get_pixmap(dpi=int(_dpi) if _dpi else 300)
                bpng = png.tobytes()

                if not nocache and _grade < 10:
                    with open(fcache_path, "wb") as f:
                        f.write(bpng)
                elif os.path.exists(fcache_path):
                    os.remove(fcache_path)

                doc.close()
                response = HttpResponse(bpng, content_type="image/png")
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
            pages = doc.pages()

            grade_int = tuple(map(lambda x: int(x), grade.split(",")))
            grade = tuple(filter(lambda y: y, grade_int))

            if grade and len(grade) != 4:
                grade = grade_int

            excludes = tuple(
                filter(lambda y: y, map(lambda x: x.strip(), anon.split(",")))
            )

            for p in pages:
                if page and p.number != page - 1:
                    continue
                r = Rect(*grade) if grade else p.rect

                # anonimização se texto
                areas_all = []
                for e in excludes:
                    areas = p.search_for(e)
                    areas_all.extend(areas)

                for area in areas_all:
                    if r.intersects(area):
                        p.add_redact_annot(area, fill=(0, 0, 0))

                p.apply_redactions()

                # anonimização se imagem

                for img in p.get_images(full=True):
                    xref = img[0]

                    # Obtém a posição e o tamanho da imagem DENTRO da página do PDF
                    # img[1] é o xref da máscara se houver, mas p.get_image_rects nos dá a área visual
                    rects = p.get_image_rects(xref)
                    if not rects:
                        continue
                    img_rect_in_page = rects[0]  # Posição da imagem na página

                    # Se houver uma grade/restrição e ela não tocar nesta imagem, pula para a próxima
                    if grade and not img_rect_in_page.intersects(r):
                        continue

                    # Extrai e abre a imagem com o Pillow
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image = Image.open(io.BytesIO(image_bytes))

                    # Calcula a escala: quantos pixels da imagem equivalem a 1 ponto do PDF
                    scale_x = image.width / img_rect_in_page.width
                    scale_y = image.height / img_rect_in_page.height

                    draw = ImageDraw.Draw(image)

                    if grade:
                        # Converte as coordenadas da 'grade' da página para os pixels reais da imagem
                        # (Subtrai a origem da imagem e multiplica pela escala do pixel)
                        pixel_x0 = (r.x0 - img_rect_in_page.x0) * scale_x
                        pixel_y0 = (r.y0 - img_rect_in_page.y0) * scale_y
                        pixel_x1 = (r.x1 - img_rect_in_page.x0) * scale_x
                        pixel_y1 = (r.y1 - img_rect_in_page.y0) * scale_y

                        draw.rectangle(
                            [pixel_x0, pixel_y0, pixel_x1, pixel_y1], fill=(0, 0, 0)
                        )
                    else:
                        # Se não há grade, pinta a imagem inteira de preto
                        draw.rectangle(
                            [0, 0, image.width, image.height], fill=(0, 0, 0)
                        )

                    # Salva em memória e atualiza imediatamente dentro do loop (indentação corrigida)
                    output = io.BytesIO()
                    image.save(output, format="PNG")

                    # Correção do erro: Chamando o update_image na indentação correta
                    p.replace_image(xref, stream=output.getvalue())

            # if settings.DEBUG:
            #    doc.save("/tmp/pdf_anon.pdf")
            #    doc.close()
            #    return
            fout = f"{fin}.new"
            doc.save(fout)
            doc.close()
            if os.path.exists(fout) and os.path.getsize(fout) > 0:
                os.remove(fin)
                os.rename(fout, fin)

        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {e}")
            pass

    def response_pdftotext(self, arquivo):

        fin = arquivo.path
        doc = pymupdf.open(fin)
        text = "\n".join([page.get_text() for page in doc])
        text = clean_text(text)

        response = HttpResponse(text, content_type="text/plain; charset=utf-8")
        return response

    def response_file(self, request, *args, **kwargs):
        self.item = item = self.get_queryset().filter(pk=kwargs["pk"]).first()
        text = request.GET.get("text", "")
        page = request.GET.get("page", 0)
        dpi = request.GET.get("dpi", 72)
        grade = request.GET.get("grade", "0")
        anon = request.GET.get("anon", "")

        try:
            dpi = int(dpi)
            dpi = min(max(dpi, 72), 300)
            opcoes_dpi = (72, 100, 150, 200, 300)
            if dpi not in opcoes_dpi:
                # se o dpi não estiver na lista, pega o mais próximo
                # (maior ou igual)
                for i in opcoes_dpi:
                    if dpi <= i:
                        dpi = i
                        break
        except Exception:
            dpi = 72

        if not item:
            logger.info(f"response_file not item")
            raise NotFound

        if not hasattr(item, self.action):
            logger.info(f"response_file not attr action")
            raise NotFound

        arquivo = getattr(item, self.action)
        if not arquivo:
            logger.info(f"response_file not file")
            raise NotFound

        mime = get_mime_type_from_file_extension(arquivo.name)

        if request.user.is_superuser and anon and mime == "application/pdf":
            self.anon(arquivo, int(page), grade, anon)

        if text and mime == "application/pdf":
            return self.response_pdftotext(arquivo)

        if page and mime == "application/pdf":
            return self.response_pagepdftoimage(arquivo, int(page), dpi, grade)

        if mime == "application/png":
            mime = "image/png"

        if mime == "application/jpg":
            mime = "image/jpg"

        if mime == "application/jpeg":
            mime = "image/jpeg"

        custom_filename = arquivo.name.split("/")[-1]
        if hasattr(self, "custom_filename"):
            custom_filename = self.custom_filename(item)

        thumbnail = (
            self.thumbnail() if self.format_kwarg and mime.startswith("image") else None
        )

        original = ""
        if "original" in request.GET and self.request.user.is_superuser:
            original = "original__"
        elif "original" in request.GET:
            raise PermissionDenied(
                "Acesso ao arquivo original permitido apenas ao Administrador do PortalCMJ."
            )

        if settings.DEBUG:
            file_path = arquivo.original_path if original else arquivo.path

            if thumbnail:
                file_path = thumbnail.path

            with open(file_path, "rb") as f:
                response = HttpResponse(f, content_type=mime)
            response["Content-Disposition"] = 'inline; filename="%s"' % custom_filename
            return response

        response = HttpResponse(content_type="%s" % mime)
        response["Content-Disposition"] = 'inline; filename="%s"' % custom_filename

        response["Cache-Control"] = "no-cache"
        response["Pragma"] = "no-cache"
        response["Expires"] = 0

        if thumbnail:
            original = ""
            arquivo = thumbnail

        response["X-Accel-Redirect"] = "/mediaredirect/{0}{1}".format(
            original, arquivo.name
        )

        logger.debug(f"response_file end method")
        return response

    def thumbnail(self):

        format = self.format_kwarg
        ext = format

        if "." in format:
            format, ext = format.split(".")
        else:
            format = None

        arquivo = getattr(self.item, self.action)

        if not format:
            return arquivo

        if format[0] != "c":
            thumbnail = get_thumbnailer(arquivo).get_thumbnail(
                {
                    "size": (int(format), int(format)),
                    "box": None,
                    "crop": False,
                    "detail": True,
                }
            )
        else:
            size = format[1:]
            thumbnail = get_thumbnailer(arquivo).get_thumbnail(
                {
                    "size": (int(size), int(size)),
                    "box": getattr(self.item, f"{self.action}_cropping"),
                    "crop": True,
                    "detail": True,
                }
            )
        return thumbnail


class ControlAccessFileForContainerMixin(ResponseFileMixin):

    def get_queryset(self):
        qs = super().get_queryset()

        u = self.request.user

        param_tip_pub = {
            "%s__tipo"
            % "__".join(
                self.container_field.split("__")[:-1]
            ): AreaTrabalho.TIPO_PUBLICO
        }

        param_user = {self.container_field: u}

        if u.is_anonymous or not u.areatrabalho_set.exists():
            qs = qs.filter(**param_tip_pub)
        else:
            if u.has_perms(self.permission_required):
                qs = qs.filter(**param_user)
            else:
                qs = qs.filter(**param_tip_pub)

        return qs
