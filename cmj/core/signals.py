import logging

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone

from cmj.core.models import Notificacao
from cmj.core.signals_functions import send_signal_for_websocket_time_refresh, \
    auditlog_signal_function, \
    notificacao_signal_function, redesocial_post_function, \
    signed_files_extraction_post_save_signal_function
from sapl.materia.models import Proposicao


logger = logging.getLogger(__name__)


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
    redesocial_post_function(sender, instance, **kwargs)


@receiver(post_save, dispatch_uid='signed_files_extraction_post_save_signal')
def signed_files_extraction_post_save_signal(sender, instance, **kwargs):
    signed_files_extraction_post_save_signal_function(
        sender, instance, **kwargs)


@receiver(pre_save, dispatch_uid='signed_files_extraction_pre_save_signal')
def signed_files_extraction_pre_save_signal(sender, instance, **kwargs):

    if not hasattr(instance, 'FIELDFILE_NAME') or not hasattr(instance, 'metadata'):
        return

    if sender == Proposicao:
        # TODO: melhorar o tratamento de reinício de extração
        if instance.data_envio:
            return

    metadata = instance.metadata
    for fn in instance.FIELDFILE_NAME:  # fn -> field_name
        ff = getattr(instance, fn)  # ff -> file_field

        if metadata and 'signs' in metadata and \
                        fn in metadata['signs'] and\
                        metadata['signs'][fn]:
            metadata['signs'][fn] = {}

        if not ff:
            continue

        try:
            meta_signs = {"running_extraction": True}

            if not metadata:
                metadata = {'signs': {}}

            if 'signs' not in metadata:
                metadata['signs'] = {}

            metadata['signs'][fn] = meta_signs
        except Exception as e:
            # print(e)
            pass

    instance.metadata = metadata
