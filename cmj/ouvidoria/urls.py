from django.conf.urls import include, url

from cmj.ouvidoria.views import DenunciaAnonimaFormView

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns_ouvidoria = [

    url(r'^fale-conosco/ouvidoria/denuncia-anonima/?$',
        DenunciaAnonimaFormView.as_view(), name='denuncia_form'),

]

urlpatterns = [
    url(r'', include(urlpatterns_ouvidoria)),


]
