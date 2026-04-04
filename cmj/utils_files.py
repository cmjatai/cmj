import os

import magic
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


TIPOS_TEXTO_PERMITIDOS = (
    "application/vnd.oasis.opendocument.text",
    "application/x-vnd.oasis.opendocument.text",
    "application/pdf",
    "application/x-pdf",
    "application/zip",
    "application/acrobat",
    "applications/vnd.pdf",
    "text/pdf",
    "text/x-pdf",
    "text/plain",
    "application/txt",
    "browser/internal",
    "text/anytext",
    "widetext/plain",
    "widetext/paragraph",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/xml",
    "application/octet-stream",
    "text/xml",
    "text/html",
    "video/mp4",
)

TIPOS_IMG_PERMITIDOS = (
    "image/jpeg",
    "image/jpg",
    "image/jpe_",
    "image/pjpeg",
    "image/vnd.swiftview-jpeg",
    "application/jpg",
    "application/x-jpg",
    "image/pjpeg",
    "image/pipeg",
    "image/vnd.swiftview-jpeg",
    "image/x-xbitmap",
    "image/bmp",
    "image/x-bmp",
    "image/x-bitmap",
    "image/png",
    "application/png",
    "application/x-png",
)


def fabrica_validador_de_tipos_de_arquivo(lista, nome):

    def restringe_tipos_de_arquivo(value):
        name_file = (
            value.path
            if hasattr(value, "path")
            else value.name if hasattr(value, "name") else ""
        )

        if not os.path.splitext(name_file)[1][:1]:
            raise ValidationError(
                _("Não é possível fazer upload de arquivos sem extensão.")
            )
        try:
            mime = magic.from_buffer(value.read(), mime=True)
            if mime not in lista:
                raise ValidationError(_("Tipo de arquivo não suportado"))
        except FileNotFoundError:
            raise ValidationError(_("Arquivo não encontrado"))

    # o nome é importante para as migrations
    restringe_tipos_de_arquivo.__name__ = nome
    return restringe_tipos_de_arquivo


restringe_tipos_de_arquivo_txt = fabrica_validador_de_tipos_de_arquivo(
    TIPOS_TEXTO_PERMITIDOS, "restringe_tipos_de_arquivo_txt"
)
restringe_tipos_de_arquivo_img = fabrica_validador_de_tipos_de_arquivo(
    TIPOS_IMG_PERMITIDOS, "restringe_tipos_de_arquivo_img"
)
