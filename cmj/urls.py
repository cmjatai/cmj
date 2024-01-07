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
from django.views.generic.base import TemplateView
from django.views.static import serve as view_static_server

import cmj.agenda.urls
import cmj.arq.urls
import cmj.cerimonial.urls
import cmj.core.urls
from cmj.core.views_short import ShortRedirectView
import cmj.diarios.urls
import cmj.globalrules.urls
import cmj.ouvidoria.urls
import cmj.sigad.urls
import cmj.videos.urls
import sapl.api.urls
import sapl.audiencia.urls
import sapl.base.urls
import sapl.comissoes.urls
import sapl.compilacao.urls
import sapl.lexml.urls
import sapl.materia.urls
import sapl.norma.urls
import sapl.painel.urls
import sapl.painelset.urls
import sapl.parlamentares.urls
import sapl.protocoloadm.urls
import sapl.redireciona_urls.urls
import sapl.relatorios.urls
import sapl.sessao.urls


urlpatterns_all = [
    url(r'^j(?P<short>[0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ]*)$',
        ShortRedirectView.as_view(), name='short_view'),

    url(r'^admin/', admin.site.urls),

    url(r'^message$', TemplateView.as_view(template_name='base.html')),
    url('', include('social_django.urls', namespace='social')),


    url(r'', include(cmj.globalrules.urls)),

    url(r'', include(cmj.core.urls)),
    url(r'', include(cmj.cerimonial.urls)),
    url(r'', include(cmj.diarios.urls)),
    url(r'', include(cmj.arq.urls)),
    url(r'', include(cmj.ouvidoria.urls)),
    url(r'', include(cmj.agenda.urls)),
    url(r'', include(cmj.videos.urls)),


    url(r'', include(sapl.audiencia.urls)),
    url(r'', include(sapl.comissoes.urls)),
    url(r'', include(sapl.sessao.urls)),
    url(r'', include(sapl.parlamentares.urls)),
    url(r'', include(sapl.materia.urls)),
    url(r'', include(sapl.norma.urls)),
    url(r'', include(sapl.lexml.urls)),
    url(r'', include(sapl.painel.urls)),
    url(r'', include(sapl.painelset.urls)),
    url(r'', include(sapl.protocoloadm.urls)),
    url(r'', include(sapl.compilacao.urls)),
    url(r'', include(sapl.relatorios.urls)),
    url(r'', include(sapl.base.urls)),

    url(r'', include(sapl.redireciona_urls.urls)),

]

admin.site.site_header = 'Cmj'

if settings.DEBUG_TOOLBAR_ACTIVE:
    import debug_toolbar
    urlpatterns_all.append(url('__debug__/', include(debug_toolbar.urls)))

if settings.DEBUG:

    # urlpatterns += static(settings.MEDIA_URL,
    #                      document_root=settings.MEDIA_ROOT)
    urlpatterns_all += static(settings.STATIC_URL,
                              document_root=settings.STATIC_ROOT)

    urlpatterns_all += [
        url(r'^media/(?P<path>.*)$', view_static_server, {
            'document_root': settings.MEDIA_ROOT,
        })
    ]


urlpatterns_all += [
    url(r'', include(sapl.api.urls)),

    # urls não tratadas até aqui será capturada por PathView de cmj.sigad
    url(r'', include(cmj.sigad.urls)),
]

urlpatterns = urlpatterns_all
