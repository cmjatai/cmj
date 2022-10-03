
from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter
from cmj.api.views import DocumentoViewSet, BiViewSet, AppVersionView


from .apps import AppConfig

app_name = AppConfig.name

router = DefaultRouter()
router.register(r'documento', DocumentoViewSet)
router.register(r'bi', BiViewSet)
#router.register(r'sessao-plenaria', SessaoPlenariaViewSet)
urlpatterns_router = router.urls

urlpatterns_api = [
]

urlpatterns = [
    url(r'^api/', include(urlpatterns_api)),
    url(r'^api/', include(urlpatterns_router)),

    url(r'^api/version', AppVersionView.as_view()),
]
