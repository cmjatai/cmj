
def area_trabalho(request):
    if request.user.is_anonymous():
        return {}

    result = {'area_trabalho': []}
    for at in request.user.area_trabalho_set.all():
        result['area_trabalho'].append({'pk': at.pk, 'nome': at.nome})
    return result
