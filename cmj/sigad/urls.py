from django.conf.urls import include, url

from cmj.sigad import views

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns_sigad = [

    url(r'^classe/create$',
        views.ClasseCreateView.as_view(), name='classe_create'),

    url(r'^classe/(?P<pk>[0-9]+)/create$',
        views.ClasseCreateView.as_view(), name='subclasse_create'),


    url(r'^classe/(?P<pk>[0-9]+)/edit$',
        views.ClasseUpdateView.as_view(), name='classe_edit'),

    url(r'^classe$',
        views.ClasseListView.as_view(), name='classe_list'),

    url(r'^classe/(?P<pk>[0-9]+)$',
        views.ClasseListView.as_view(), name='subclasse_list'),

    url(r'^documento/pm_import$',
        views.DocumentoPmImportView.as_view(), name='documento_pm_import'),

    url(r'^documento/(?P<pk>[0-9]+)'
        '/media\.?(?P<resize>\w+)?/(?P<media_id>[0-9]+)$',
        views.MediaDetailView.as_view(), name='media_get'),

    url(r'^(?P<slug>.*)$',
        views.PathView.as_view(), name='path_view'),
]

urlpatterns = [
    url(r'', include(urlpatterns_sigad))

]
"""
urlpatterns_sigad = [

    url(r'^classe/import',
        views.Pcasp2016ImportView.as_view(), name='pcasp2016_import'),

    url(r'^classe/create$',
        views.ClasseCreateView.as_view(), name='classe_create'),

    url(r'^documento/create$',
        views.DocumentoCreateView.as_view(), name='documento_create'),

    url(r'^documento/(?P<pk>[0-9]+)$',
        views.DocumentoDetailView.as_view(), name='documento_detail'),


]

urlpatterns = [
    url(r'^sigad/', include(urlpatterns_sigad))

]"""
