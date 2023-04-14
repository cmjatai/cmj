from django.conf.urls import include, url

from cmj.arq import views
from cmj.core.views import app_vue_view

from .apps import AppConfig


app_name = AppConfig.name
urlpatterns_arq = [

    url(r'^draft$',
        app_vue_view, name='app_vue_draft_view_url'),

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

]

urlpatterns = [
    url(r'^arq/', include(urlpatterns_arq)),
]
