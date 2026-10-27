from django.conf import settings


def areatrabalho(request):
    if request.user.is_anonymous:
        return {}
    result = {"areatrabalho": []}
    for at in request.user.areatrabalho_set.all():
        result["areatrabalho"].append({"pk": at.pk, "nome": at.nome})
    return result


def debug(request):
    return {"DEBUG": settings.DEBUG}


def base_url(request):
    return {"base_url": settings.BASE_URL}


def debug_and_remote_database(request):
    return {
        "DEBUG_AND_REMOTE_DATABASE": settings.DEBUG
        and not settings.DEV_HOST_NAME in settings.DATABASES["default"]["HOST"],
    }
