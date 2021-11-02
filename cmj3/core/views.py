from django.conf import settings
from django.http.response import HttpResponse, Http404
from django.shortcuts import render


def service_worker(request):
    try:
        response = HttpResponse(
            open(settings.PWA_SERVICE_WORKER_PATH).read(),
            content_type='application/javascript'
        )
    except:
        raise Http404
    return response
