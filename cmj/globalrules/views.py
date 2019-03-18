import json

from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import render


def service_worker(request):
    response = HttpResponse(open(settings.PWA_SERVICE_WORKER_PATH).read(
    ), content_type='application/javascript')
    return response


def offline(request):
    return render(request, "offline.html")


def manifest(request):
    try:
        f = open(settings.PWA_MANIFEST_PATH).read()
        response = HttpResponse(f, content_type='application/json')
        return response
    except:
        return render(request, 'manifest.json')
