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
from django.views.generic.base import TemplateView, RedirectView
from django.views.static import serve as view_static_server

import cmj.agenda.urls
import cmj.api.urls
import cmj.cerimonial.urls
import cmj.core.urls
import cmj.diarios.urls
import cmj.globalrules.urls
import cmj.ouvidoria.urls
import cmj.procuradoria.urls
import cmj.sigad.urls
import sapl.api.urls
import sapl.audiencia.urls
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


#import sapl.api.urls
# import sapl.api.urls
urlpatterns = [
    # FIXME: eliminar redirecionamento em 2019
    url(r'^portal/?$', RedirectView.as_view(url='/')),
    url(r'^admin/', admin.site.urls),

    url(r'^message$', TemplateView.as_view(template_name='base.html')),
    url('', include('social_django.urls', namespace='social')),


    url(r'', include(cmj.globalrules.urls)),

    # Todo o conjunto de urls que passarão por adaptação do sapl
    # devem ficar antes do sapl. para isso criar a app cmj.sapl_adapter

    url(r'', include(cmj.core.urls)),
    url(r'', include(cmj.cerimonial.urls)),
    url(r'', include(cmj.diarios.urls)),
    url(r'', include(cmj.ouvidoria.urls)),
    url(r'', include(cmj.agenda.urls)),
    url(r'', include(cmj.procuradoria.urls)),


    url(r'^sapl/', include(sapl.audiencia.urls)),
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
    url(r'', include(sapl.base.urls)),
    url(r'', include(sapl.api.urls)),


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


urlpatterns += [
    url(r'', include(cmj.api.urls)),

    # urls não tratadas até aqui será capturada por PathView de cmj.sigad
    url(r'', include(cmj.sigad.urls)),
]
