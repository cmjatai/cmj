import json

from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import render


def service_worker(request):
    if settings.DEBUG:
        sw_file = settings.PROJECT_DIR_FRONTEND_2018.child(
            'src', 'assets', 'v2018', 'service-worker.js')
    else:
        sw_file = settings.PROJECT_DIR_FRONTEND_2018.child('dist', 'v2018', 'service-worker.js')
    response = HttpResponse(open(sw_file).read())
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
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
