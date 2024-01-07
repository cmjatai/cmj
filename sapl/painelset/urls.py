from django.conf.urls import url
from django.urls.conf import include

from sapl.painelset.views import PainelSETCrud, TelaCrud, ComponenteBaseCrud

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns = [

    url(r'^painelset', include(PainelSETCrud.get_urls())),


    url(r'^painelset/configs/tela', include(TelaCrud.get_urls())),
    url(r'^painelset/configs/componentebase',
        include(ComponenteBaseCrud.get_urls())),

]
