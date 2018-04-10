from django.conf import settings
from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from cmj.api.views import DocumentoViewSet

from .apps import AppConfig


app_name = AppConfig.name


router = DefaultRouter()
router.register(r'documento', DocumentoViewSet)
#router.register(r'sessao-plenaria', SessaoPlenariaViewSet)
urlpatterns_router = router.urls

urlpatterns_api = [


]

if settings.DEBUG:
    urlpatterns_api += [
        url(r'^docs', include('rest_framework_docs.urls')), ]

urlpatterns = [
    url(r'^api/', include(urlpatterns_api)),
    url(r'^api/', include(urlpatterns_router))
]
