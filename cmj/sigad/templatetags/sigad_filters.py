from django import template
from cmj.sigad.models import CaixaPublicacao, Documento, Classe
from cmj.utils import time_of_period


register = template.Library()


@register.simple_tag
def verbose_name(instance, field_name):
    return instance._meta.get_field(field_name).verbose_name.title()


@register.filter
def organize_avatars(pos, total):
    map_arranjo = {
        '0': 1,
        '1': 1,
        '2': 1,
        '3': 2,
        '4': 2,
        '5': 2,
        '6': 2,
        '7': 2,
        '8': 2,
        '9': 2, }
    return pos % map_arranjo[str(total if total <= 9 else 9)] == 0


@register.filter
def organize_direction_avatars(pos, total):
    map_arranjo = {
        '0': 1,
        '1': 1,
        '2': 2,
        '3': 2,
        '4': 2,
        '5': 3,
        '6': 3,
        '7': 4,
        '8': 4,
        '9': 4}
    return pos % map_arranjo[str(total if total <= 9 else 9)] == 0


@register.filter
def organize_direction_horizontal_avatars(pos, total):
    map_arranjo = {
        '0': 1,
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 2,
        '5': 3,
        '6': 3,
        '7': 4,
        '8': 4,
        '9': 5}
    return pos % map_arranjo[str(total if total <= 9 else 9)] == 0


@register.filter
def inspect(obj):

    return obj.__dict__


@register.filter
def caixa_publicacao(key, classe):
    try:
        cp = CaixaPublicacao.objects.get(key=key, classe=classe)
        docs = cp.caixapublicacaorelationship_set.all()
        result = {'url_edit': 'cmj.sigad:caixapublicacao%s_update' % ('classe' if classe else ''),
                  'cp': cp, 'docs':
                  list(
                      map(lambda x: (
                          x.documento, x.documento.nodes.filter(
                            tipo=Documento.TPD_IMAGE).order_by('parent__ordem', 'ordem').first()),
                          docs
                          ))
                  }

        return result
    except:
        return None


@register.filter
def caixa_publicacao_popup(key, request):
    try:
        cks = request.COOKIES
        gets = request.GET

        if 'popup_closed' in cks or 'popup' in gets:
            return False

        excludes = []
        for k, pk in cks.items():
            if 'popup_viewed_' in k:
                excludes.append(pk)

        classe = Classe.objects.get(slug='popup')
        cp = CaixaPublicacao.objects.get(key=key, classe=classe)
        docs = cp.caixapublicacaorelationship_set.exclude(id__in=excludes)

        result = {'url_edit': 'cmj.sigad:caixapublicacao%s_update' % ('classe' if classe else ''),
                  'cp': cp, 'docs':
                  list(
                      map(lambda x: (
                          x.documento,
                          x.documento.nodes.filter(
                              tipo=Documento.TPD_IMAGE).order_by('ordem').first(),
                          x.id),
                          docs
                          ))
                  }

        return result
    except:
        return None


@register.filter
def video_duration(jdata):

    j = jdata

    if not j or 'contentDetails' not in j or 'duration' not in j['contentDetails']:
        return ''

    d = j['contentDetails']['duration']

    return time_of_period(d)
