from django.conf import settings
from django.conf.urls import include, url
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from cmj.api.views import DocumentoViewSet, BiViewSet, AppVersionView,\
    recria_token

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

if settings.PYTHON_VERSION >= settings.PYTHON_VERSION_MIN_FOR_JWT:
    urlpatterns.append(
        url(r'^api/token$', TokenObtainPairView.as_view(), name='token_obtain_pair'))
    urlpatterns.append(
        url(r'^api/token/refresh$', TokenRefreshView.as_view(), name='token_refresh'))
else:
    urlpatterns.append(
        url(r'^api/token$', obtain_auth_token, name="api_token_auth"))
    urlpatterns.append(
        url(r'^api/token/refresh$/(?P<pk>\d*)$', recria_token, name="recria_token"))
