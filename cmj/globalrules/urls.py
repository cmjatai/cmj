from django.urls.conf import path, re_path

from cmj.globalrules.views import manifest, offline, service_worker_proxy

urlpatterns = [
    path(
        "v6/service-worker.js",
        service_worker_proxy,
        name="serviceworker_proxy_v6",
    ),
    path("service-worker.js", service_worker_proxy, name="serviceworker_proxy_v2018"),
    path("v6/manifest.json", manifest, name="manifest"),
    #    re_path('^offline/$', offline, name='offline')
]
