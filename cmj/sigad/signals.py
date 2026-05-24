from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from cmj.sigad.models import CaixaPublicacao, Classe, Documento
from cmj.utils import delete_django_cache_pattern


@receiver([post_save, post_delete], sender=Classe)
@receiver([post_save, post_delete], sender=Documento)
@receiver([post_save, post_delete], sender=CaixaPublicacao)
def signal_post_sigad(sender, **kwargs):
    keys = [
        make_template_fragment_key("portalcmj_tc_pagina_inicial_parte1"),
        make_template_fragment_key("portalcmj_tc_pagina_inicial_parte3"),
        make_template_fragment_key("portalcmj_tc_pagina_inicial_servicos"),
        make_template_fragment_key("portalcmj_tc_acesso_informacao"),
    ]
    for key in keys:
        cache.delete(key)
    delete_django_cache_pattern("portalcmj_c_menu_publico")
    delete_django_cache_pattern("portalcmj_tc_transparencia")
