import logging

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch.dispatcher import receiver

from cmj.core.models import Notificacao
from cmj.core.signals_functions import signed_files_extraction_function,\
    send_signal_for_websocket_time_refresh, auditlog_signal_function,\
    notificacao_signal_function, redesocial_post_function


logger = logging.getLogger(__name__)


@receiver(pre_save, dispatch_uid='signed_files_extraction_pre_save_signal')
def signed_files_extraction_pre_save_signal(sender, instance, **kwargs):
    signed_files_extraction_function(sender, instance, **kwargs)


@receiver([post_save, post_delete], dispatch_uid='timerefresh_post_signal')
def timerefresh_post_signal(sender, instance, **kwargs):
    send_signal_for_websocket_time_refresh(instance, **kwargs)


@receiver([post_save, post_delete], dispatch_uid='auditlog_post_signal')
def auditlog_post_signal(sender, **kwargs):
    auditlog_signal_function(sender, **kwargs)


@receiver(post_save, sender=Notificacao, dispatch_uid='notificacao_post_signal')
def notificacao_post_signal(sender, instance, **kwargs):
    notificacao_signal_function(sender, instance, **kwargs)


@receiver(post_save, dispatch_uid='redesocial_post_signal')
def redesocial_post_signal(sender, instance, **kwargs):
    return
    redesocial_post_function(sender, instance, **kwargs)
