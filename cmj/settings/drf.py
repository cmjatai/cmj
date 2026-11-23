from .zenv import config

REST_FRAMEWORK = {
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FileUploadParser",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "drfautoapi.PDFRenderer",
        "drfautoapi.PngRenderer",
        "drfautoapi.JpgRenderer",
        "drfautoapi.JpegRenderer",
    ),
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "drfautoapi.DrfautoapiNegotiation",
    "DEFAULT_PERMISSION_CLASSES": ("sapl.api.permissions.SaplModelPermissions",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "sapl.api.schema.Schema",
    "DEFAULT_PAGINATION_CLASS": "sapl.api.pagination.StandardPagination",
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework.filters.SearchFilter",
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
}

# TODO:
# rate limiting for API requests
# https://www.django-rest-framework.org/api-guide/throttling/


# "rest_framework.permissions.IsAuthenticated",

# Teto de itens de uma lista pedida com get_all=true por quem não tem a permissão
# list_ do model (docs/specs/api/paginacao-custo.md)
API_GET_ALL_MAX_ITEMS = config("API_GET_ALL_MAX_ITEMS", cast=int, default=2000)

DRFAUTOAPI = {
    "DEFAULT_SERIALIZER_MODULE": "cmj.api.serializers,sapl.api.serializers",
    "DEFAULT_FILTER_MODULE": "cmj.api.forms,sapl.api.forms",
    "GLOBAL_SERIALIZER_MIXIN": "cmj.api.serializers.CmjSerializerMixin",
    "GLOBAL_FILTERSET_MIXIN": "cmj.api.forms.CmjFilterSetMixin",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "PortalCMJ API - docs",
    "DESCRIPTION": "API de dados abertos do PortalCMJ. Documentação dos modelos, seus atributos, filtros de busca e endpoint's de comunicação RestFULL.",
    "VERSION": "1.0.0",
}
