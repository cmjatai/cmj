from django.urls.conf import re_path
from cmj.globalrules.views import service_worker, manifest, offline

urlpatterns = [
    re_path('^service-worker.js$', service_worker, name='serviceworker'),
    re_path('^manifest.json$', manifest, name='manifest'),
    re_path('^offline/$', offline, name='offline')
]
