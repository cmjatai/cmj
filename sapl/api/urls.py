from django.urls.conf import include, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.authtoken.views import obtain_auth_token

from cmj.api.views import (
    AppSessionAuthView,
    AppVersionView,
    CmjApiViewSetConstrutor,
    DocumentoViewSet,
)
from sapl.api.views import SaplApiViewSetConstrutor, recria_token

from .apps import AppConfig

app_name = AppConfig.name

router_sapl = SaplApiViewSetConstrutor.router()
router_cmj = CmjApiViewSetConstrutor.router()

router_cmj.register(r"documento", DocumentoViewSet)

urlpatterns_router = router_sapl.urls + router_cmj.urls

urlpatterns_api_doc = [
    re_path(
        "^schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="sapl.api:schema_api"),
        name="swagger_ui_schema_api",
    ),
    re_path(
        "^schema/redoc/",
        SpectacularRedocView.as_view(url_name="sapl.api:schema_api"),
        name="redoc_schema_api",
    ),
    re_path("^schema/", SpectacularAPIView.as_view(), name="schema_api"),
]

urlpatterns = [
    re_path(r"^api/", include(urlpatterns_api_doc)),
    re_path(r"^api/", include(urlpatterns_router)),
    re_path(r"^api/version", AppVersionView.as_view()),
    re_path(r"^api/auth/token", obtain_auth_token),
    re_path(r"^api/auth/session", AppSessionAuthView.as_view()),
    re_path(r"^api/recriar-token/(?P<pk>\d*)$", recria_token, name="recria_token"),
]
