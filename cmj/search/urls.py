from django.urls.conf import re_path
from django.views.generic.base import RedirectView

from cmj.search.views import CmjSearchView, MateriaSearchView, NormaSearchView

from .apps import AppConfig


app_name = AppConfig.name


urlpatterns = [

    re_path(r'^pesquisar$', RedirectView.as_view(
        url='/pesquisar/'), name='haystack_redirect_search'),

    re_path(r'^pesquisar/$', CmjSearchView(), name='haystack_search'),

    re_path(r'^pesquisar/materia$', MateriaSearchView(),
        name='materia_haystack_search'),

    re_path(r'^pesquisar/norma$', NormaSearchView(), name='norma_haystack_search'),

]
