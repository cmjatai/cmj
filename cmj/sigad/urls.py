from django.urls.conf import re_path, include

from cmj.core.views_short import ShortAdminCrud
from cmj.sigad import views
from cmj.sigad.views import PermissionsUserClasseCrud,\
    PermissionsUserDocumentoCrud, CaixaPublicacaoCrud,\
    CaixaPublicacaoClasseCrud

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns_sigad = [

    re_path(r'^short', include(ShortAdminCrud.get_urls())),

    re_path(r'^classe/create$',
        views.ClasseCreateView.as_view(), name='classe_create'),

    re_path(r'^classe/(?P<pk>[0-9]+)/create$',
        views.ClasseCreateView.as_view(), name='subclasse_create'),


    re_path(r'^classe/(?P<pk>[0-9]+)/edit$',
        views.ClasseUpdateView.as_view(), name='classe_edit'),

    re_path(r'^classe/(?P<pk>[0-9]+)/delete',
        views.ClasseDeleteView.as_view(), name='classe_delete'),

    re_path(r'^classe$',
        views.ClasseListView.as_view(), name='classe_list'),



    re_path(r'^classe/(?P<pk>[0-9]+)$',
        views.ClasseListView.as_view(), name='subclasse_list'),


    re_path(r'^classe/(?P<pk>[0-9]+)/documento/create$',
        views.DocumentoCreateView.as_view(), name='documento_create'),

    re_path(r'^classe/(?P<pk>[0-9]+)/documento/construct$',
        views.DocumentoConstructCreateView.as_view(),
        name='documento_construct_create'),

    re_path(r'^documento/(?P<pk>[0-9]+)/construct$',
        views.DocumentoConstructView.as_view(), name='documento_construct'),

    re_path(r'^documento/(?P<pk>[0-9]+)/edit$',
        views.DocumentoUpdateView.as_view(), name='documento_edit'),

    re_path(r'^documento/(?P<pk>[0-9]+)/delete$',
        views.DocumentoDeleteView.as_view(), name='documento_delete'),

    re_path(r'^documento', include(PermissionsUserDocumentoCrud.get_urls())),
    re_path(r'^caixapublicacao', include(CaixaPublicacaoCrud.get_urls())),
    re_path(r'^classe', include(PermissionsUserClasseCrud.get_urls() +
                            CaixaPublicacaoClasseCrud.get_urls()
                            )),

]

urlpatterns = [
    re_path(r'', include(urlpatterns_sigad)),


    re_path(r'^$',
        views.PaginaInicialView.as_view(), name='pagina_inicial_view'),

    re_path(r'^parlamentar/?(?P<parlamentar>[^/.]*)/?(?P<slug>[^.]*)\.?(?P<resize>\d+)?(\.midia)?\.?(?P<page>\w+)?$',
        views.PathParlamentarView.as_view(), name='path_parlamentar_view'),

    re_path(r'^(?P<slug>[^.]*)\.?(?P<resize>\d+)?(\.midia)?\.?(?P<page>\w+)?$',
        views.PathView.as_view(), name='path_view'),

]
"""
urlpatterns_sigad = [

    re_path(r'^classe/import',
        views.Pcasp2016ImportView.as_view(), name='pcasp2016_import'),

    re_path(r'^classe/create$',
        views.ClasseCreateView.as_view(), name='classe_create'),

    re_path(r'^documento/create$',
        views.DocumentoCreateView.as_view(), name='documento_create'),

    re_path(r'^documento/(?P<pk>[0-9]+)$',
        views.DocumentoDetailView.as_view(), name='documento_detail'),


]

urlpatterns = [
    re_path(r'^sigad/', include(urlpatterns_sigad))

]"""
