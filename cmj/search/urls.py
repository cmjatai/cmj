from django.conf.urls import url
from django.views.generic.base import RedirectView

from cmj.search.views import CmjSearchView, MateriaSearchView, NormaSearchView

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [

    url(r'^pesquisar$', RedirectView.as_view(
        url='/pesquisar/'), name='haystack_redirect_search'),

    url(r'^pesquisar/$', CmjSearchView(), name='haystack_search'),

    url(r'^pesquisar/materia$', MateriaSearchView(),
        name='materia_haystack_search'),

    url(r'^pesquisar/norma$', NormaSearchView(), name='norma_haystack_search'),

]
