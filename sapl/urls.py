"""sapl URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.urls.conf import re_path, include
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView, TemplateView
from django.views.static import serve as view_static_server

import sapl.api.urls
import sapl.audiencia.urls
import sapl.base.urls
import sapl.comissoes.urls
import sapl.compilacao.urls
import sapl.materia.urls
import sapl.norma.urls
import sapl.painel.urls
import sapl.parlamentares.urls
import sapl.protocoloadm.urls
import sapl.redireciona_urls.urls
import sapl.relatorios.urls
import sapl.sessao.urls

urlpatterns = [
    re_path(r'^$', TemplateView.as_view(template_name='index.html'),
        name='sapl_index'),
    re_path(r'^message$', TemplateView.as_view(template_name='base.html')),
    re_path(r'^admin/', include(admin.site.urls)),

    re_path(r'', include(sapl.comissoes.urls)),
    re_path(r'', include(sapl.sessao.urls)),
    re_path(r'', include(sapl.parlamentares.urls)),
    re_path(r'', include(sapl.materia.urls)),
    re_path(r'', include(sapl.norma.urls)),
    re_path(r'', include(sapl.painel.urls)),
    re_path(r'', include(sapl.protocoloadm.urls)),
    re_path(r'', include(sapl.compilacao.urls)),
    re_path(r'', include(sapl.relatorios.urls)),
    re_path(r'', include(sapl.audiencia.urls)),

    # must come at the end
    #   so that base /sistema/ url doesn't capture its children
    re_path(r'', include(sapl.base.urls)),

    re_path(r'', include(sapl.api.urls)),

    re_path(r'^favicon\.ico$', RedirectView.as_view(
        url='/static/sapl/img/favicon.ico', permanent=True)),

    re_path(r'', include(sapl.redireciona_urls.urls)),
]


# Fix a static asset finding error on Django 1.9 + gunicorn:
# http://stackoverflow.com/questions/35510373/

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),

    ]
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', view_static_server, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
