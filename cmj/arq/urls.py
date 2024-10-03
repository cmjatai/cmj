from django.urls.conf import re_path, include

from cmj.arq import views
from cmj.arq.views_search import ArqSearchView
from cmj.core.views import app_vue_view

from .apps import AppConfig


app_name = AppConfig.name
urlpatterns_arq = [

    re_path(r'^classe/create$',
        views.ArqClasseCreateView.as_view(), name='arqclasse_create'),

    re_path(r'^classe/(?P<pk>[0-9]+)/create$',
        views.ArqClasseCreateView.as_view(), name='subarqclasse_create'),

    re_path(r'^classe/(?P<pk>[0-9]+)/edit$',
        views.ArqClasseUpdateView.as_view(), name='arqclasse_edit'),

    re_path(r'^classe/(?P<pk>[0-9]+)/delete',
        views.ArqClasseDeleteView.as_view(), name='arqclasse_delete'),

    re_path(r'^classe$',
        views.ArqClasseListView.as_view(), name='arqclasse_list'),

    re_path(r'^classe/(?P<pk>[0-9]+)$',
        views.ArqClasseListView.as_view(), name='subarqclasse_list'),

    re_path(r'^classe/(?P<classe_id>[0-9]+)/doc/(?P<pk>[0-9]+)/edit$',
        views.ArqDocUpdateView.as_view(), name='arqdoc_edit'),

    re_path(r'^classe/(?P<classe_id>[0-9]+)/doc/(?P<pk>[0-9]+)/delete$',
        views.ArqDocDeleteView.as_view(), name='arqdoc_delete'),

    re_path(r'^classe/(?P<classe_id>[0-9]+)/doc/(?P<pk>[0-9]+)$',
        views.ArqDocDetailView.as_view(), name='arqdoc_detail'),


    re_path(r'^classe/(?P<classe_id>[0-9]+)/doc/create$',
        views.ArqDocCreateView.as_view(), name='arqdoc_create'),

    re_path(r'^classe/(?P<classe_id>[0-9]+)/doc/bulk_create$',
        views.ArqDocBulkCreateView.as_view(), name='arqdoc_bulk_create'),

    re_path(r'^pesquisa/$', ArqSearchView(), name='haystack_arqsearch'),


]

urlpatterns = [
    re_path(r'^arqadmin/', include(urlpatterns_arq)),

    re_path(r'^arq/(?P<slug>[^.]*)$',
        app_vue_view, name='app_vue_arq_view_url'),

]
