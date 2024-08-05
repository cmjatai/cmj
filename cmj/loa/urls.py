from django.conf.urls import url, include

from cmj.loa.views import LoaCrud

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [
    url(r'^loa',
        include(LoaCrud.get_urls())
        ),
]
