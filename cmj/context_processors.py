from django.conf import settings


def areatrabalho(request):
    if request.user.is_anonymous():
        return {}
    result = {'areatrabalho': []}
    for at in request.user.areatrabalho_set.areatrabalho_de_parlamentares():
        result['areatrabalho'].append({'pk': at.pk, 'nome': at.nome})
    return result


def debug(context):
    return {'DEBUG': settings.DEBUG}


def site_url(context):
    return {'site_url': settings.SITE_URL}
