import re

from django.http.response import Http404
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.renderers import BaseRenderer


class DrfautoapiNegotiation(DefaultContentNegotiation):

    def filter_renderers(self, renderers, format):

        renderers = [renderer for renderer in renderers
                     if re.match(renderer.format, format)]
        if not renderers:
            raise Http404
        return renderers


class FilesRenderer(BaseRenderer):

    def render(self, data, accepted_media_type = None, renderer_context = None):
        raise Http404


class JpgRenderer(FilesRenderer):
    media_type = 'image/jpg'
    format = r'[a-zA-Z0-9]*\.?jpg'


class PngRenderer(FilesRenderer):
    media_type = 'image/png'
    format = r'[a-zA-Z0-9]*\.?png'


class PDFRenderer(FilesRenderer):
    media_type = 'application/pdf'
    format = 'pdf'
