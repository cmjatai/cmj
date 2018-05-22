from django import template
from cmj.sigad.models import CaixaPublicacao, Documento


register = template.Library()


"""@register.simple_tag
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
    return pos % map_arranjo[str(total if total <= 9 else 9)] == 0"""
