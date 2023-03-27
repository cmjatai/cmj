from django.conf.urls import include, url

from cmj.arq import views
from cmj.core.views import app_vue_view

from .apps import AppConfig


app_name = AppConfig.name
urlpatterns_arq = [

    url(r'^draft$',
        app_vue_view, name='app_vue_draft_view_url'),
]
"""urlpatterns_arq = [

    url(r'^classe/create$',
        views.ClasseCreateView.as_view(), name='classe_create'),

    url(r'^classe/(?P<pk>[0-9]+)/create$',
        views.ClasseCreateView.as_view(), name='subclasse_create'),


    url(r'^classe/(?P<pk>[0-9]+)/edit$',
        views.ClasseUpdateView.as_view(), name='classe_edit'),

    url(r'^classe/(?P<pk>[0-9]+)/delete',
        views.ClasseDeleteView.as_view(), name='classe_delete'),

    url(r'^classe$',
        views.ClasseListView.as_view(), name='classe_list'),



    url(r'^classe/(?P<pk>[0-9]+)$',
        views.ClasseListView.as_view(), name='subclasse_list'),

]
"""
urlpatterns = [
    url(r'^arq/', include(urlpatterns_arq)),
]
