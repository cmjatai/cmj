import json

import requests
from django.conf import settings
from django.http.response import HttpResponse
from django.shortcuts import render


def service_worker_proxy_dev_old(request):
    if settings.DEBUG and "dev" in request.path:
        host, port = request.get_host().split(":")
        host = "cmjfront2018" if port == "9099" else host
        try:
            try:
                response = requests.get(
                    f"http://{host}:8080/service-worker-dev.js", timeout=5
                )
                response = HttpResponse(response.content)
            except Exception:
                response = HttpResponse(
                    "/* Service Worker not found on dev server (port 8080) */"
                )
        except ImportError:
            response = HttpResponse("/* Requests library not found */")
    else:
        sw_file = settings.PROJECT_DIR_FRONTEND_2018.child(
            "dist", "v2018", "service-worker.js"
        )
        response = HttpResponse(open(sw_file).read())

    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


# Frontends Vite: prefixo da URL -> (diretório do frontend, container dev, porta dev)
VITE_FRONTENDS = {
    "v6": ("PROJECT_DIR_FRONTEND_2026", "cmjfront2026", 5173),
    "v8": ("PROJECT_DIR_FRONTEND_V8", "cmjfrontv8", 5174),
}


def _vite_frontend(request):
    for version in VITE_FRONTENDS:
        if request.path.startswith(f"/{version}/"):
            return version
    return None


def service_worker_proxy(request):

    content = ""

    version = _vite_frontend(request)

    sw_2018_file = settings.PROJECT_DIR_FRONTEND_2018.child(
        "dist", "v2018", "service-worker.js"
    )

    if version:
        dir_setting, dev_container, dev_port = VITE_FRONTENDS[version]
        sw_vite_file = getattr(settings, dir_setting).child(
            "dist", version, "service-worker.js"
        )
        sw_allowed = f"/{version}/"
    else:
        sw_allowed = "/"

    if settings.DEBUG:

        host, port = request.get_host().split(":")

        if version:
            host = dev_container if port == "9099" else host
            url = f"http://{host}:{dev_port}/static/service-worker.js"
            sw_file = sw_vite_file
        else:
            host = "cmjfront2018" if port == "9099" else host
            url = f"http://{host}:8080/service-worker.js"
            sw_file = sw_2018_file

        try:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    content = response.content
            except Exception:
                if sw_file.exists():
                    content = open(sw_file).read()
        except ImportError:
            content = "/* Requests library not found */"

        response = HttpResponse(content)
        response.headers["Service-Worker-Allowed"] = sw_allowed

    else:
        sw_file = sw_vite_file if version else sw_2018_file
        response = HttpResponse(open(sw_file).read())
        response.headers["Service-Worker-Allowed"] = sw_allowed

    response.headers["Content-Type"] = "application/javascript"
    return response


def offline(request):
    return render(request, "offline.html")


def manifest(request):
    try:
        version = _vite_frontend(request) or "v6"
        dir_setting = VITE_FRONTENDS[version][0]
        f = open(
            getattr(settings, dir_setting).child("dist", version, "manifest.json")
        ).read()
        response = HttpResponse(f, content_type="application/json")
        return response
    except:
        return render(request, "manifest.json")
