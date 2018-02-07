from django import template
from cmj.sigad.models import CaixaPublicacao, Documento


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
        '9': 2}
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
def caixa_publicacao(key, classe):
    try:
        cp = CaixaPublicacao.objects.get(key=key, classe=classe)
        docs = cp.documentos.order_by('-public_date')
        result = {'cp': cp, 'docs':
                  list(
                      map(lambda x: (
                          x, x.nodes.filter(
                            tipo=Documento.TPD_IMAGE).order_by('ordem').first()),
                          docs
                          ))
                  }

        return result
    except:
        return None
