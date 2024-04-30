from django.conf.urls import url
from django.views.generic.base import RedirectView

from cmj.search.views import CmjSearchView

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [

    url(r'^pesquisar$', RedirectView.as_view(
        url='/pesquisar/'), name='haystack_redirect_search'),

    url(r'^pesquisar/$', CmjSearchView(), name='haystack_search'),

]
