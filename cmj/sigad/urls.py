from django.conf.urls import include, url

from cmj.core.views_short import ShortAdminCrud
from cmj.sigad import views
from cmj.sigad.views import PermissionsUserClasseCrud,\
    PermissionsUserDocumentoCrud, CaixaPublicacaoCrud,\
    CaixaPublicacaoClasseCrud

from .apps import AppConfig


app_name = AppConfig.name

urlpatterns_sigad = [

    url(r'^short', include(ShortAdminCrud.get_urls())),

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


    url(r'^classe/(?P<pk>[0-9]+)/documento/create$',
        views.DocumentoCreateView.as_view(), name='documento_create'),

    url(r'^classe/(?P<pk>[0-9]+)/documento/construct$',
        views.DocumentoConstructCreateView.as_view(),
        name='documento_construct_create'),

    url(r'^documento/(?P<pk>[0-9]+)/construct$',
        views.DocumentoConstructView.as_view(), name='documento_construct'),

    url(r'^documento/(?P<pk>[0-9]+)/edit$',
        views.DocumentoUpdateView.as_view(), name='documento_edit'),

    url(r'^documento/(?P<pk>[0-9]+)/delete$',
        views.DocumentoDeleteView.as_view(), name='documento_delete'),

    url(r'^documento', include(PermissionsUserDocumentoCrud.get_urls())),
    url(r'^caixapublicacao', include(CaixaPublicacaoCrud.get_urls())),
    url(r'^classe', include(PermissionsUserClasseCrud.get_urls() +
                            CaixaPublicacaoClasseCrud.get_urls()
                            )),

]

urlpatterns = [
    url(r'', include(urlpatterns_sigad)),


    url(r'^$',
        views.PaginaInicialView.as_view(), name='pagina_inicial_view'),

    url(r'^parlamentar/?(?P<parlamentar>[^/.]*)/?(?P<slug>[^.]*)\.?(?P<resize>\d+)?(\.midia)?\.?(?P<page>\w+)?$',
        views.PathParlamentarView.as_view(), name='path_parlamentar_view'),

    url(r'^(?P<slug>[^.]*)\.?(?P<resize>\d+)?(\.midia)?\.?(?P<page>\w+)?$',
        views.PathView.as_view(), name='path_view'),

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
