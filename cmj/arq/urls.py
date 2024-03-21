from django.conf.urls import include, url

from cmj.arq import views
from cmj.arq.views_search import ArqSearchView
from cmj.core.views import app_vue_view

from .apps import AppConfig


app_name = AppConfig.name
urlpatterns_arq = [

    url(r'^classe/create$',
        views.ArqClasseCreateView.as_view(), name='arqclasse_create'),

    url(r'^classe/(?P<pk>[0-9]+)/create$',
        views.ArqClasseCreateView.as_view(), name='subarqclasse_create'),

    url(r'^classe/(?P<pk>[0-9]+)/edit$',
        views.ArqClasseUpdateView.as_view(), name='arqclasse_edit'),

    url(r'^classe/(?P<pk>[0-9]+)/delete',
        views.ArqClasseDeleteView.as_view(), name='arqclasse_delete'),

    url(r'^classe$',
        views.ArqClasseListView.as_view(), name='arqclasse_list'),

    url(r'^classe/(?P<pk>[0-9]+)$',
        views.ArqClasseListView.as_view(), name='subarqclasse_list'),

    url(r'^classe/(?P<classe_id>[0-9]+)/doc/(?P<pk>[0-9]+)/edit$',
        views.ArqDocUpdateView.as_view(), name='arqdoc_edit'),

    url(r'^classe/(?P<classe_id>[0-9]+)/doc/(?P<pk>[0-9]+)/delete',
        views.ArqDocDeleteView.as_view(), name='arqdoc_delete'),

    url(r'^classe/(?P<classe_id>[0-9]+)/doc/(?P<pk>[0-9]+)',
        views.ArqDocDetailView.as_view(), name='arqdoc_detail'),


    url(r'^classe/(?P<classe_id>[0-9]+)/doc/create$',
        views.ArqDocCreateView.as_view(), name='arqdoc_create'),

    url(r'^search/', ArqSearchView(), name='haystack_arqsearch'),


]

urlpatterns = [
    url(r'^arqadmin/', include(urlpatterns_arq)),

    url(r'^arq/(?P<slug>[^.]*)$',
        app_vue_view, name='app_vue_arq_view_url'),

]
