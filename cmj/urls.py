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
    1. Import the include() function: from django.urls.conf import re_path, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))

re_path(r'^sapl/', include(sapl.comissoes.urls)),
re_path(r'^sapl/', include(sapl.sessao.urls)),
re_path(r'^sapl/', include(sapl.parlamentares.urls)),
re_path(r'^sapl/', include(sapl.materia.urls)),
re_path(r'^sapl/', include(sapl.norma.urls)),
re_path(r'^sapl/', include(sapl.lexml.urls)),
re_path(r'^sapl/', include(sapl.painel.urls)),
re_path(r'^sapl/', include(sapl.protocoloadm.urls)),
re_path(r'^sapl/', include(sapl.compilacao.urls)),
re_path(r'^sapl/', include(sapl.relatorios.urls)),
re_path(r'^sapl/', include(sapl.base.urls)),"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls.conf import re_path, include
from django.views.generic.base import TemplateView
from cmj.dashboard.registry import dashboard


import cmj.agenda.urls
import cmj.arq.urls
import cmj.cerimonial.urls
import cmj.core.urls
from cmj.core.views_short import ShortRedirectView
import cmj.diarios.urls
import cmj.globalrules.urls
import cmj.loa.urls
import cmj.ouvidoria.urls
import cmj.search.urls
import cmj.sigad.urls
import cmj.videos.urls
import cmj.painelset.urls
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
import sapl.redireciona_urls.urls
import sapl.relatorios.urls
import sapl.sessao.urls


urlpatterns_all = [
    re_path(r'^j(?P<short>[0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ]*)$',
            ShortRedirectView.as_view(), name='short_view'),

    re_path(r'^admin/', admin.site.urls),

    re_path(r'^message$', TemplateView.as_view(template_name='base.html')),

    re_path('', include('social_django.urls', namespace='social')),

    re_path(r'', include(cmj.globalrules.urls)),

    re_path(r'', include(cmj.core.urls)),
    re_path(r'', include(cmj.cerimonial.urls)),
    re_path(r'', include(cmj.diarios.urls)),
    re_path(r'', include(cmj.loa.urls)),
    re_path(r'', include(cmj.arq.urls)),
    re_path(r'', include(cmj.ouvidoria.urls)),
    re_path(r'', include(cmj.agenda.urls)),
    re_path(r'', include(cmj.videos.urls)),
    re_path(r'', include(cmj.painelset.urls)),

    re_path(r'', include(sapl.audiencia.urls)),
    re_path(r'', include(sapl.comissoes.urls)),
    re_path(r'', include(sapl.sessao.urls)),
    re_path(r'', include(sapl.parlamentares.urls)),
    re_path(r'', include(sapl.materia.urls)),
    re_path(r'', include(sapl.norma.urls)),
    re_path(r'', include(sapl.lexml.urls)),
    re_path(r'', include(sapl.painel.urls)),
    re_path(r'', include(sapl.protocoloadm.urls)),
    re_path(r'', include(sapl.compilacao.urls)),
    re_path(r'', include(sapl.relatorios.urls)),
    re_path(r'', include(sapl.base.urls)),

    re_path(r'', include(sapl.redireciona_urls.urls)),

    re_path("dash/", dashboard.urls),
]

admin.site.site_header = 'PortalCMJ'

if settings.DEBUG_TOOLBAR_ACTIVE:
    urlpatterns_all += [
        re_path('silk/', include('silk.urls', namespace='silk')),
        re_path('__debug__/', include('debug_toolbar.urls')),
    ]

if settings.DEBUG:
    urlpatterns_all.append(
        re_path(r'^debug.html$', TemplateView.as_view(template_name='debug.html')))

    urlpatterns_all += static(settings.STATIC_URL,
                              document_root=settings.STATIC_ROOT)

urlpatterns_all += [
    re_path(r'', include(sapl.api.urls)),

    re_path(r'', include(cmj.search.urls)),

    # urls não tratadas até aqui será capturada por PathView de cmj.sigad
    re_path(r'', include(cmj.sigad.urls)),
]

urlpatterns = urlpatterns_all
