from django.urls.conf import re_path, path
from cmj.globalrules.views import service_worker_proxy, manifest, offline

urlpatterns = [
     path('v2025/service-worker.js', service_worker_proxy, name='serviceworker_proxy_v2025'),
     re_path('^service-worker\.js$', service_worker_proxy, name='serviceworker_proxy_v2018'),
     path('v2025/manifest.json', manifest, name='manifest'),
#    re_path('^offline/$', offline, name='offline')
]
