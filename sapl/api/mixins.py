import hashlib
import io
import logging
import os
import re

import pymupdf
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse, JsonResponse
from easy_thumbnails.files import get_thumbnailer
from PIL import Image, ImageDraw
from pymupdf import Rect
from rest_framework.exceptions import NotAuthenticated, NotFound
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied

from cmj.core.models import AreaTrabalho
from cmj.core.services.s_areatrabalho import AreaTrabalhoService
from cmj.utils import clean_text
from sapl.utils import get_mime_type_from_file_extension

logger = logging.getLogger(__name__)

logger_xaccel = logging.getLogger("XAccelRedirect")


class ValorInvalido(Exception):
    """Valor inválido num parâmetro ou no sufixo de uma action de arquivo."""


class ResponseFileMixin:
    # controle de permissão de responsabilidade da view que utiliza este mixin
    # este mixin apenas fornece métodos auxiliares para manipulação e resposta de arquivos,
    # como conversão de páginas de PDF para imagens e anonimização de conteúdo.
    # Ele não realiza validações de permissão ou autenticação, que devem ser tratadas na view que o utiliza.
    # Portanto, é responsabilidade da view garantir que o usuário tenha acesso adequado aos arquivos manipulados por este mixin.

    def response_pagepdftoimage(self, arquivo, _page, _dpi, _grade="0"):

        # nocache é auxílio de manutenção: só vale para superusuário
        nocache = (
            bool(self.request.GET.get("nocache")) and self.request.user.is_superuser
        )

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
            # a imagem guardada só vale enquanto for mais nova que o arquivo
            cache_valido = os.path.exists(fcache_path) and os.path.getmtime(
                fcache_path
            ) >= os.path.getmtime(arquivo.path)
            if not nocache and cache_valido:
                with open(fcache_path, "rb") as f:
                    response = HttpResponse(f, content_type="image/png")
                self.log(
                    self.request, response, _type=f"pdftopng-page-{_page}-dpi-{_dpi}"
                )
                return response
            elif os.path.exists(fcache_path):
                os.remove(fcache_path)

        doc = pymupdf.open(arquivo.file)
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

                self.log(
                    self.request, response, _type=f"pdftopng-page-{_page}-dpi-{_dpi}"
                )
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
                    fmt_original = base_image["ext"]  # Ex: "jpeg" ou "png"
                    image = Image.open(io.BytesIO(image_bytes))

                    # Converte para RGB caso seja JPEG e esteja em outro formato interno
                    if fmt_original.upper() in ["JPEG", "JPG"] and image.mode != "RGB":
                        image = image.convert("RGB")

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
                    save_format = (
                        "JPEG" if fmt_original.lower() in ["jpg", "jpeg"] else "PNG"
                    )
                    image.save(output, format=save_format)

                    # Correção do erro: Chamando o update_image na indentação correta
                    p.replace_image(xref, stream=output.getvalue())

                    p.add_redact_annot(img_rect_in_page, fill=None)
                    p.apply_redactions(images=0)

            # if settings.DEBUG:
            #    doc.save("/tmp/pdf_anon.pdf")
            #    doc.close()
            #    return
            fout = f"{fin}.new"
            doc.save(
                fout,
                garbage=4,
                deflate=True,
                use_objstms=True,
            )
            doc.close()
            if os.path.exists(fout) and os.path.getsize(fout) > 0:
                os.remove(fin)
                os.rename(fout, fin)

        except Exception as e:
            logger_xaccel.error(f"Erro ao processar arquivo: {e}")
            pass

    pdftotext_cache_timeout = 60 * 60 * 24 * 7

    def response_pdftotext(self, arquivo):

        fin = arquivo.path

        # o texto extraído fica no cache enquanto o arquivo não mudar
        stat = os.stat(fin)
        versao = f"{fin}:{stat.st_mtime_ns}:{stat.st_size}"
        key = "sapl.api.pdftotext:" + hashlib.md5(versao.encode()).hexdigest()

        text = cache.get(key)
        if text is None:
            doc = pymupdf.open(fin)
            text = "\n".join([page.get_text() for page in doc])
            text = clean_text(text)
            cache.set(key, text, self.pdftotext_cache_timeout)

        response = HttpResponse(text, content_type="text/plain; charset=utf-8")

        self.log(self.request, response, _type="pdftotext")
        return response

    # limite técnico do tamanho de miniatura pedido no sufixo
    thumbnail_tamanho_maximo = 99999

    @staticmethod
    def inteiro(valor):
        """Inteiro sem sinal escrito só com algarismos; None se não for."""
        if not (valor.isascii() and valor.isdigit()):
            return None
        try:
            return int(valor)
        except ValueError:
            # mais algarismos do que o int() aceita converter
            return None

    def response_file(self, request, *args, **kwargs):
        # valor inválido sai como resposta pronta em JSON, com ou sem sufixo
        # de arquivo na URL
        try:
            return self._response_file(request, *args, **kwargs)
        except ValorInvalido as e:
            return JsonResponse({"detail": str(e)}, status=400)

    def _response_file(self, request, *args, **kwargs):
        self.request = request
        self.item = item = self.get_queryset().filter(pk=kwargs["pk"]).first()
        text = request.GET.get("text", "")
        page = request.GET.get("page", "")
        dpi = request.GET.get("dpi", 72)
        grade = request.GET.get("grade") or "0"
        anon = request.GET.get("anon", "")

        if page:
            page = self.inteiro(page)
            if page is None:
                raise ValorInvalido("O parâmetro page deve ser um número inteiro.")
        else:
            page = None

        # grade é auxílio de manutenção: só vale para superusuário
        if not request.user.is_superuser:
            grade = "0"
        else:
            partes = grade.split(",")
            if len(partes) not in (1, 4) or None in map(self.inteiro, partes):
                raise ValorInvalido(
                    "O parâmetro grade deve ser um número inteiro ou quatro "
                    "inteiros separados por vírgula."
                )

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
            logger_xaccel.info(f"response_file not item")
            raise NotFound

        if not hasattr(item, self.action):
            logger_xaccel.info(f"response_file not attr action")
            raise NotFound

        arquivo = getattr(item, self.action)
        if not arquivo:
            logger_xaccel.info(f"response_file not file")
            raise NotFound

        mime = get_mime_type_from_file_extension(arquivo.name)

        if request.user.is_superuser and anon and mime == "application/pdf":
            if not self.is_direct_navigation(request):
                raise PermissionDenied(
                    "A anonimização só é aceita por navegação direta: digite a "
                    "URL na barra de endereço ou abra-a de um favorito."
                )
            self.anon(arquivo, page or 0, grade, anon)

        if text and mime == "application/pdf":
            return self.response_pdftotext(arquivo)

        if page is not None and mime == "application/pdf":
            # sem autenticação, só a primeira página é entregue como imagem
            if page > 1 and not request.user.is_authenticated:
                raise NotAuthenticated(
                    "Só a primeira página é entregue como imagem sem autenticação."
                )
            return self.response_pagepdftoimage(arquivo, page, dpi, grade)

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
            response["Cache-Control"] = "no-cache"
            response["Pragma"] = "no-cache"
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

        self.log(request, response)

        return response

    @staticmethod
    def is_direct_navigation(request):
        """A requisição é uma navegação iniciada pelo próprio usuário (URL
        digitada ou favorito), e não um link de outra página, uma imagem
        embutida ou um script. Vale o que o navegador informa nos cabeçalhos
        Fetch Metadata; sem eles, não é navegação direta."""
        meta = request.META
        return (
            meta.get("HTTP_SEC_FETCH_SITE") == "none"
            and meta.get("HTTP_SEC_FETCH_MODE") == "navigate"
            and meta.get("HTTP_SEC_FETCH_DEST") == "document"
        )

    def log(self, request, response, _type="download"):
        user = request.user.id if request.user.is_authenticated else "anonymous"
        logger_xaccel.info(
            f"[{request.META.get('HTTP_X_REAL_IP')}] "
            f"User: {user} "
            f"Media: {response.get('X-Accel-Redirect', _type)} "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT')} "
            f"Referer: {request.META.get('HTTP_REFERER')} "
        )

    def thumbnail(self):

        format = self.format_kwarg

        arquivo = getattr(self.item, self.action)

        # sufixo só com a extensão: o arquivo como está
        if "." not in format:
            return arquivo

        pedido = re.fullmatch(r"(c?)([0-9]+)\.[a-zA-Z0-9]+", format)
        size = self.inteiro(pedido.group(2)) if pedido else None
        if size is None or not 1 <= size <= self.thumbnail_tamanho_maximo:
            raise ValorInvalido(
                "Tamanho de miniatura inválido: use <n>.<ext> ou c<n>.<ext>, "
                f"com n de 1 a {self.thumbnail_tamanho_maximo}."
            )

        if not pedido.group(1):
            thumbnail = get_thumbnailer(arquivo).get_thumbnail(
                {
                    "size": (size, size),
                    "box": None,
                    "crop": False,
                    "detail": True,
                }
            )
        else:
            if not hasattr(self.item, f"{self.action}_cropping"):
                raise ValorInvalido(
                    "Este arquivo não tem recorte: peça a miniatura sem o prefixo c."
                )
            thumbnail = get_thumbnailer(arquivo).get_thumbnail(
                {
                    "size": (size, size),
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


class RegistrosDaAreaDoOperadorMixin:
    """Viewset de model ligado a área de trabalho: como nas telas, o usuário
    alcança só os registros das áreas em que opera, e só grava nelas
    (docs/specs/api/acesso.md)."""

    area_field = "workspace"

    def get_queryset(self):
        return AreaTrabalhoService.registros_do_operador(
            self.request.user, super().get_queryset(), self.area_field
        )

    def _confere_area(self, serializer, criando):
        dados = serializer.validated_data
        if not criando and self.area_field not in dados:
            return
        area = dados.get(self.area_field)
        if not AreaTrabalhoService.opera_na_area(self.request.user, area):
            raise DRFPermissionDenied(
                "Só o operador da área de trabalho grava registros nela."
            )

    def perform_create(self, serializer):
        self._confere_area(serializer, criando=True)
        serializer.save()

    def perform_update(self, serializer):
        self._confere_area(serializer, criando=False)
        serializer.save()
