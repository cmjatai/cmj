import json

from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import render
import requests


def service_worker_proxy_dev_old(request):
    if settings.DEBUG and 'dev' in request.path:
        host, port = request.get_host().split(':')
        host ='cmjfront2018' if port == '9099' else host
        try:
            try:
                response = requests.get(f'http://{host}:8080/service-worker-dev.js', timeout=5)
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

def service_worker_proxy(request):

    content = ''

    is_v2025 = 'v2025' in request.path

    sw_2018_file = settings.PROJECT_DIR_FRONTEND_2018.child('dist', 'v2018', 'service-worker.js')
    sw_2025_file = settings.PROJECT_DIR_FRONTEND_2025.child('dist', 'v2025', 'service-worker.js')

    if settings.DEBUG:

        host, port = request.get_host().split(':')

        if is_v2025:
            host ='cmjfront2025' if port == '9099' else host
            url = f'http://{host}:5173/static/service-worker.js'
            sw_file = sw_2025_file
        else:
            host ='cmjfront2018' if port == '9099' else host
            url = f'http://{host}:8080/service-worker.js'
            sw_file = sw_2018_file

        try:
            try:
                response = requests.get(url, timeout=5)
                content = response.content
            except Exception:
                content = open(sw_file).read()
        except ImportError:
            content = "/* Requests library not found */"

        response = HttpResponse(content)
        response.headers['Service-Worker-Allowed'] = '/v2025/' if is_v2025 else '/'

    else:
        sw_file = sw_2025_file if is_v2025 else sw_2018_file
        response = HttpResponse(open(sw_file).read())
        response.headers['Service-Worker-Allowed'] = '/v2025/' if is_v2025 else '/'

    response.headers['Content-Type'] = 'application/javascript'
    return response


def offline(request):
    return render(request, "offline.html")


def manifest(request):
    try:
        f = open(settings.PROJECT_DIR_FRONTEND_2025.child('dist', 'v2025', 'manifest.json')).read()
        response = HttpResponse(f, content_type='application/json')
        return response
    except:
        return render(request, 'manifest.json')
