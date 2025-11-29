import logging

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch.dispatcher import receiver

from cmj.core.models import Notificacao
from cmj.core.signals_functions import auditlog_signal_function, \
    notificacao_signal_function, redesocial_post_function, \
    signed_files_extraction_post_signal_function, \
    signed_files_extraction_pre_signal_function


logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], dispatch_uid='signal_post_auditlog')
def signal_post_auditlog(sender, **kwargs):
    auditlog_signal_function(sender, **kwargs)


@receiver(post_save, sender=Notificacao, dispatch_uid='signal_post_notificacao')
def signal_post_notificacao(sender, instance, **kwargs):
    notificacao_signal_function(sender, instance, **kwargs)


@receiver(post_save, dispatch_uid='signal_post_redesocial')
def signal_post_redesocial(sender, instance, **kwargs):
    redesocial_post_function(sender, instance, **kwargs)


@receiver(post_save, dispatch_uid='signal_post_signed_files_extraction')
def signal_post_signed_files_extraction(sender, instance, **kwargs):
    signed_files_extraction_post_signal_function(
        sender, instance, **kwargs)


@receiver(pre_save, dispatch_uid='signal_pre_signed_files_extraction')
def signal_pre_signed_files_extraction(sender, instance, **kwargs):
    signed_files_extraction_pre_signal_function(
        sender, instance, **kwargs)
