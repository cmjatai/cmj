from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from cmj.sigad.models import CaixaPublicacao, Classe, Documento

@receiver([post_save, post_delete], sender=Classe)
@receiver([post_save, post_delete], sender=Documento)
@receiver([post_save, post_delete], sender=CaixaPublicacao)
def signal_post_sigad(sender, **kwargs):
    keys = [
        make_template_fragment_key('portalcmj_pagina_inicial_parte1'),
        make_template_fragment_key('portalcmj_pagina_inicial_parte3'),
        make_template_fragment_key('portalcmj_acesso_informacao'),
        make_template_fragment_key('portalcmj_menu_publico'),
    ]
    for key in keys:
        cache.delete(key)

