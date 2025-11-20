import json

from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import render
import requests


def service_worker_proxy(request):
    if settings.DEBUG and 'dev' in request.path:
        try:
            try:
                response = requests.get('http://localhost:8080/service-worker-dev.js', timeout=5)
                response = HttpResponse(response.content)
            except Exception:
                response = HttpResponse("/* Service Worker not found on dev server (port 8080) */")
        except ImportError:
            response = HttpResponse("/* Requests library not found */")
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
