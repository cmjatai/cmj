import logging

from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver

from sapl.sessao import tasks
from sapl.sessao.models import RegistroVotacao, SessaoPlenaria


logger = logging.getLogger(__name__)


@receiver(post_save, sender=RegistroVotacao, dispatch_uid='signal_sessao_registrovotacao')
def signal_sessao_registrovotacao(sender, instance, **kwargs):
    if not settings.DEBUG or (
            settings.DEBUG and settings.FOLDER_DEBUG_CONTAINER == settings.PROJECT_DIR):
        tasks.task_add_selo_votacao.apply_async(
            ([instance.pk, ], ),
            countdown=5
        )
    else:
        tasks.task_add_selo_votacao_function([instance.pk,])


@receiver([post_save, post_delete], sender=SessaoPlenaria)
def signal_sessao_sessaoplenaria(sender, **kwargs):
    keys = [
        make_template_fragment_key('portalcmj_pagina_inicial_parte1'),
        make_template_fragment_key('portalcmj_sessoes_futuras'),
    ]
    for key in keys:
        cache.delete(key)

