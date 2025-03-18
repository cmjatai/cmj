import logging

from django.conf import settings
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch.dispatcher import receiver

from sapl.sessao import tasks
from sapl.sessao.models import RegistroVotacao


logger = logging.getLogger(__name__)


@receiver(post_save, sender=RegistroVotacao, dispatch_uid='registrovotacao_post_signal')
def registrovotacao_post_signal(sender, instance, **kwargs):

    if not settings.DEBUG or (
            settings.DEBUG and settings.FOLDER_DEBUG_CONTAINER == settings.PROJECT_DIR):
        tasks.task_add_selo_votacao.apply_async(
            ([instance.pk, ], ),
            countdown=5
        )
    else:
        tasks.task_add_selo_votacao_function([instance.pk,])
