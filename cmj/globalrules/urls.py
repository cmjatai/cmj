from django.urls.conf import re_path, path
from cmj.globalrules.views import service_worker_proxy, manifest, offline

urlpatterns = [
     path('v2026/service-worker.js', service_worker_proxy, name='serviceworker_proxy_v2026'),
     re_path('^service-worker\.js$', service_worker_proxy, name='serviceworker_proxy_v2018'),
     path('v2026/manifest.json', manifest, name='manifest'),
#    re_path('^offline/$', offline, name='offline')
]
