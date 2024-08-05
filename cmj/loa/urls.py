from django.conf.urls import url, include

from cmj.loa.views import LoaCrud, EmendaLoaCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    url(r'^loa',
        include(
            LoaCrud.get_urls() +
            EmendaLoaCrud.get_urls()
        )
        ),
]
