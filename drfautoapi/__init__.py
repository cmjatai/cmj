import re

from django.http.response import Http404
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.renderers import BaseRenderer, JSONRenderer


class DrfautoapiNegotiation(DefaultContentNegotiation):

    def filter_renderers(self, renderers, format):

        # o formato pedido tem de casar por inteiro com o do renderer
        renderers = [
            renderer for renderer in renderers if re.fullmatch(renderer.format, format)
        ]
        if not renderers:
            raise Http404
        return renderers


class FilesRenderer(BaseRenderer):
    """Renderer das URLs com sufixo de arquivo. O arquivo sai como resposta
    pronta, sem passar por aqui; o que chega é a resposta de erro de uma
    action de arquivo, entregue em JSON com o status dela."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        if response is not None and response.status_code >= 400:
            response["Content-Type"] = "application/json"
            return JSONRenderer().render(data)
        raise Http404


class JpegRenderer(FilesRenderer):
    media_type = "image/jpeg"
    format = r"[a-zA-Z0-9]*\.?(jpeg|jpg)"


class JpgRenderer(FilesRenderer):
    media_type = "image/jpg"
    format = r"[a-zA-Z0-9]*\.?(jpg|jpeg)"


class PngRenderer(FilesRenderer):
    media_type = "image/png"
    format = r"[a-zA-Z0-9]*\.?png"


class PDFRenderer(FilesRenderer):
    media_type = "application/pdf"
    format = "pdf"
