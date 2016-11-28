"""CMJ URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
#url('', include('django.contrib.auth.urls', namespace='auth')),
# url(r'^sapl/', include(sapl.urls)),
"""
url(r'^sapl/', include(sapl.comissoes.urls)),
url(r'^sapl/', include(sapl.sessao.urls)),
url(r'^sapl/', include(sapl.parlamentares.urls)),
url(r'^sapl/', include(sapl.materia.urls)),
url(r'^sapl/', include(sapl.norma.urls)),
url(r'^sapl/', include(sapl.lexml.urls)),
url(r'^sapl/', include(sapl.painel.urls)),
url(r'^sapl/', include(sapl.protocoloadm.urls)),
url(r'^sapl/', include(sapl.compilacao.urls)),
url(r'^sapl/', include(sapl.relatorios.urls)),
url(r'^sapl/', include(sapl.base.urls)),"""

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.static import serve as view_static_server
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailsearch import urls as wagtailsearch_urls
import sapl.api.urls
import sapl.base.urls
import sapl.comissoes.urls
import sapl.compilacao.urls
import sapl.lexml.urls
import sapl.materia.urls
import sapl.norma.urls
import sapl.painel.urls
import sapl.parlamentares.urls
import sapl.protocoloadm.urls
import sapl.relatorios.urls
import sapl.sessao.urls

import cmj.cerimonial.urls
import cmj.core.urls


urlpatterns = [
    url(r'^django-admin/', admin.site.urls),

    url('', include('social.apps.django_app.urls', namespace='social')),

    url(r'', include(cmj.core.urls)),
    url(r'', include(cmj.cerimonial.urls)),

    url(r'', include(sapl.comissoes.urls)),
    url(r'', include(sapl.sessao.urls)),
    url(r'', include(sapl.parlamentares.urls)),
    url(r'', include(sapl.materia.urls)),
    url(r'', include(sapl.norma.urls)),
    url(r'', include(sapl.lexml.urls)),
    url(r'', include(sapl.painel.urls)),
    url(r'', include(sapl.protocoloadm.urls)),
    url(r'', include(sapl.compilacao.urls)),
    url(r'', include(sapl.relatorios.urls)),
    url(r'', include(sapl.api.urls)),
    url(r'^sapl/', include(sapl.base.urls)),

    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^search_wagtail/', include(wagtailsearch_urls)),
    url(r'^documentos/', include(wagtaildocs_urls)),
    url(r'', include(wagtail_urls)),

]

admin.site.site_header = 'Cmj'

if settings.DEBUG:
    # urlpatterns += static(settings.MEDIA_URL,
    #                      document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)

    urlpatterns += [
        url(r'^media/(?P<path>.*)$', view_static_server, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]