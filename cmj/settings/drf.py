REST_FRAMEWORK = {

    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ),

    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "drfautoapi.PDFRenderer",
        "drfautoapi.PngRenderer",
        "drfautoapi.JpgRenderer",
        "drfautoapi.JpegRenderer",
    ),
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "drfautoapi.DrfautoapiNegotiation",
    "DEFAULT_PERMISSION_CLASSES": (
        "sapl.api.permissions.SaplModelPermissions",
    ),

    "DEFAULT_AUTHENTICATION_CLASSES": (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),

    'DEFAULT_SCHEMA_CLASS': 'sapl.api.schema.Schema',

    "DEFAULT_PAGINATION_CLASS":
        "sapl.api.pagination.StandardPagination",

    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework.filters.SearchFilter",
        "django_filters.rest_framework.DjangoFilterBackend",
    ),

}
# "rest_framework.permissions.IsAuthenticated",

DRFAUTOAPI = {
    'DEFAULT_SERIALIZER_MODULE': 'sapl.api.serializers',
    'DEFAULT_FILTER_MODULE': 'sapl.api.forms',
    'GLOBAL_SERIALIZER_MIXIN': 'sapl.api.serializers.CmjSerializerMixin',
    'GLOBAL_FILTERSET_MIXIN': 'sapl.api.forms.SaplFilterSetMixin'
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'PortalCMJ API - docs',
    'DESCRIPTION': "API de dados abertos do PortalCMJ. Documentação dos modelos, seus atributos, filtros de busca e endpoint's de comunicação RestFULL.",
    'VERSION': '1.0.0',
}
