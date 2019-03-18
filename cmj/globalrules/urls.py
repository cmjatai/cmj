from django.conf.urls import url
from cmj.globalrules.views import service_worker, manifest, offline

urlpatterns = [
    url('^service-worker.js$', service_worker, name='serviceworker'),
    url('^manifest.json$', manifest, name='manifest'),
    url('^offline/$', offline, name='offline')
]
