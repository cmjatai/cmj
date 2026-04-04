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
    "image/x-xbitmap",
    "image/bmp",
    "image/x-bmp",
    "image/x-bitmap",
    "image/png",
    "application/png",
    "application/x-png",
)


TIPOS_MIDIAS_PERMITIDOS = {
    "application/pdf": "pdf",
    "application/x-pdf": "pdf",
    "application/acrobat": "pdf",
    "applications/vnd.pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.oasis.opendocument.text": "odt",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.oasis.opendocument.spreadsheet": "ods",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/jpe_": "jpg",
    "image/pjpeg": "jpg",
    "image/vnd.swiftview-jpeg": "jpg",
    "application/jpg": "jpg",
    "application/x-jpg": "jpg",
    "image/pjpeg": "jpg",
    "image/pipeg": "jpg",
    "image/gif": "gif",
    "image/png": "png",
    "application/png": "png",
    "application/x-png": "png",
    "image/tiff": "tiff",
}


def fabrica_validador_de_tipos_de_arquivo(lista, nome):

    def restringe_tipos_de_arquivo(value):
        mime = magic.from_buffer(value.read(), mime=True)
        if mime not in lista:
            raise ValidationError(_("Tipo de arquivo não suportado"))
        return mime, lista[mime]

    # o nome é importante para as migrations
    restringe_tipos_de_arquivo.__name__ = nome
    return restringe_tipos_de_arquivo


restringe_tipos_de_arquivo_txt_function = fabrica_validador_de_tipos_de_arquivo(
    TIPOS_TEXTO_PERMITIDOS, "restringe_tipos_de_arquivo_txt"
)
restringe_tipos_de_arquivo_img_function = fabrica_validador_de_tipos_de_arquivo(
    TIPOS_IMG_PERMITIDOS, "restringe_tipos_de_arquivo_img"
)

restringe_tipos_de_arquivo_midias_function = fabrica_validador_de_tipos_de_arquivo(
    TIPOS_MIDIAS_PERMITIDOS, "restringe_tipos_de_arquivo_midias"
)


def restringe_tipos_de_arquivo_txt(value):
    return restringe_tipos_de_arquivo_txt_function(value)


def restringe_tipos_de_arquivo_img(value):
    return restringe_tipos_de_arquivo_img_function(value)


def restringe_tipos_de_arquivo_midias(value):
    return restringe_tipos_de_arquivo_midias_function(value)
