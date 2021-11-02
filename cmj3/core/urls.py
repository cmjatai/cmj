
from django.urls.conf import path
from .views import service_worker

urlpatterns = [
    path('service-worker.js', service_worker, name='serviceworker'),
]
