from datetime import timedelta, date, datetime
import logging

from django.apps import apps
from django.conf import settings
from django.core.serializers import serialize
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone

from cmj.core.functions_for_signals import send_mail,\
    signed_name_and_date_extract_pre_save, audit_log_function
from cmj.core.models import Notificacao
from cmj.core.tasks_redes_sociais import task_send_rede_social
from cmj.settings import EMAIL_SEND_USER


for app in apps.get_app_configs():
    for model in app.get_models():
        if hasattr(model, 'FIELDFILE_NAME') and hasattr(model, 'metadata'):
            pre_save.connect(
                signed_name_and_date_extract_pre_save,
                sender=model,
                dispatch_uid='cmj_pre_save_signed_{}_{}'.format(
                    app.name.replace('.', '_'),
                    model._meta.model_name
                )
            )


@receiver(post_save, dispatch_uid='post_save_rede_social')
def post_save_rede_social(sender, instance, using, **kwargs):
    # if not hasattr(instance, '_meta') or \
    #    instance._meta.app_config is None or \
    #        not instance._meta.app_config.name in settings.BUSINESS_APPS:
    #    return

    if not hasattr(instance, 'metadata'):
        return

    redes = [
        'telegram'
    ]

    for i, r in enumerate(redes, 1):
        md = instance.metadata
        if not md:
            md = {}

        if 'send' in md and r in md['send']:
            return

        s = md.get('send', {r: None})

        if r in s and s[r]:
            return

        for d in ('data', 'data_apresentacao', 'public_date'):
            if hasattr(instance, d):
                d = getattr(instance, d)
                if not d:
                    return
                if isinstance(d, datetime):
                    d = d.date()

                if d < date(2022, 9, 7):
                    return

        now = timezone.now()

        s[r] = now
        md['send'] = s
        instance.metadata = md
        instance.save()

        td = timedelta(seconds=1 + 10 * i)

        task_send_rede_social.apply_async(
            (r, serialize('json', [instance]), ),
            eta=now + td
        )


@receiver(post_save, sender=Notificacao, dispatch_uid='notificacao_post_save')
def notificacao_post_save(sender, instance, using, **kwargs):
    if hasattr(instance, 'not_send_mail') and instance.not_send_mail:
        return

    if instance.user.be_notified_by_email:
        send_mail(
            instance.content_object.email_notify['subject'],
            'email/notificacao_%s_%s.html' % (
                instance.content_object._meta.app_label,
                instance.content_object._meta.model_name
            ),
            {'notificacao': instance}, EMAIL_SEND_USER, instance.user.email)

        print('Uma Notificação foi enviada %s - user: %s - user_origin: %s' % (
            instance.pk,
            instance.user,
            instance.user_origin))


@receiver(post_delete)
def audit_log_post_delete(sender, **kwargs):
    audit_log_function(sender, operation='D', **kwargs)


@receiver(post_save)
def audit_log_post_save(sender, **kwargs):
    operation = 'C' if kwargs.get('created') else 'U'
    audit_log_function(sender, operation=operation, **kwargs)
