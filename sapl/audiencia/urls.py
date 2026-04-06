from django.urls.conf import include, re_path

from sapl.audiencia.views import AnexoAudienciaPublicaCrud, AudienciaCrud, index

from .apps import AppConfig

app_name = AppConfig.name

urlpatterns = [
    re_path(
        r"^audiencia",
        include(AudienciaCrud.get_urls() + AnexoAudienciaPublicaCrud.get_urls()),
    ),
]
