from django.urls.conf import include, re_path
from drf_spectacular.views import SpectacularRedocView, SpectacularSwaggerView

from cmj.api.views import (
    AppSessionAuthView,
    AppTokenAuthView,
    AppVersionView,
    DocumentoViewSet,
)
from sapl.api.views import SaplApiViewSetConstrutor, recria_token
from sapl.api.views_schema import CachedSchemaAPIView

from .apps import AppConfig

app_name = AppConfig.name

# um router só: SaplApiViewSetConstrutor e CmjApiViewSetConstrutor são a
# mesma classe, com o mesmo registro de viewsets
router = SaplApiViewSetConstrutor.router()
router.register(r"documento", DocumentoViewSet)

urlpatterns_router = router.urls

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
    re_path("^schema/", CachedSchemaAPIView.as_view(), name="schema_api"),
]

urlpatterns = [
    re_path(r"^api/", include(urlpatterns_api_doc)),
    re_path(r"^api/", include(urlpatterns_router)),
    re_path(r"^api/version", AppVersionView.as_view()),
    re_path(r"^api/auth/token", AppTokenAuthView.as_view()),
    re_path(r"^api/auth/session", AppSessionAuthView.as_view()),
    re_path(r"^api/recriar-token/(?P<pk>\d*)$", recria_token, name="recria_token"),
]
