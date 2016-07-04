
def areatrabalho(request):
    if request.user.is_anonymous():
        return {}
    result = {'areatrabalho': []}
    for at in request.user.areatrabalho_set.all():
        result['areatrabalho'].append({'pk': at.pk, 'nome': at.nome})
    return result
