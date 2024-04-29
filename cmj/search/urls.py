from django.conf.urls import url

from cmj.search.views import CmjSearchView

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [

    url(r'^search/', CmjSearchView(), name='haystack_search'),

]
