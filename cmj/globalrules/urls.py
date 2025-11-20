from django.urls.conf import re_path
from cmj.globalrules.views import service_worker_proxy, manifest, offline

urlpatterns = [
     re_path('^service-worker-dev\.js$', service_worker_proxy, name='serviceworker_proxy_dev'),
     re_path('^service-worker\.js$', service_worker_proxy, name='serviceworker_proxy_prod'),
#    re_path('^manifest.json$', manifest, name='manifest'),
#    re_path('^offline/$', offline, name='offline')
]
