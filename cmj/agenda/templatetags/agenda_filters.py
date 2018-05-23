

from datetime import datetime

from django import template

from cmj.agenda.models import Evento


register = template.Library()


@register.filter
def proximos_eventos(qtd):
    today = datetime.today().replace(hour=0,
                                     minute=0,
                                     second=0,
                                     microsecond=0)
    r = Evento.objects.filter(inicio__gte=today).order_by('inicio')[:qtd]

    return r


"""
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
