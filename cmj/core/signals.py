
import inspect
import json
import logging

from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail.message import EmailMultiAlternatives
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch.dispatcher import receiver
from django.template import loader

from cmj.core.models import Notificacao, AuditLog, OcrMyPDF, Bi
from cmj.settings import EMAIL_SEND_USER
from cmj.sigad.models import ShortRedirect
from cmj.utils import signed_name_and_date_extract


def send_mail(subject, email_template_name,
              context, from_email, to_email):

    # if settings.DEBUG:
    #    print('DEBUG: Envio Teste', subject, from_email, to_email)
    #    return

    subject = ''.join(subject.splitlines())

    html_email = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, '', from_email, [to_email])
    email_message.attach_alternative(html_email, 'text/html')
    email_message.send()


@receiver(post_save, sender=Notificacao, dispatch_uid='notificacao_post_save')
def notificacao_post_save(sender, instance, using, **kwargs):

    import inspect
    funcs = list(filter(lambda x: x == 'revision_pre_delete_signal',
                        map(lambda x: x[3], inspect.stack())))

    if funcs:
        return

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


def signed_name_and_date_extract_pre_save(sender, instance, using, **kwargs):

    if not hasattr(instance, 'FIELDFILE_NAME') or not hasattr(instance, 'metadata'):
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
            file = ff.file.file
            meta_signs = {}
            if not isinstance(ff.file, InMemoryUploadedFile):
                original_absolute_path = ff.original_path
                with open(original_absolute_path, "rb") as file:
                    meta_signs = signed_name_and_date_extract(
                        file
                    )
                    file.close()

                absolute_path = ff.path
                with open(absolute_path, "rb") as file:
                    sign_hom = signed_name_and_date_extract(
                        file
                    )
                    file.close()
                    meta_signs['hom'] = sign_hom['hom']

            else:
                file.seek(0)
                meta_signs = signed_name_and_date_extract(
                    file
                )

            if not meta_signs:
                continue

            if not metadata:
                metadata = {'signs': {}}

            if 'signs' not in metadata:
                metadata['signs'] = {}

            metadata['signs'][fn] = meta_signs
        except Exception as e:
            # print(e)
            pass

    instance.metadata = metadata


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
            # print('cmj_pre_save_signed_{}_{}'.format(
            #    app.name.replace('.', '_'),
            #    model._meta.model_name
            #))


def audit_log_function(sender, **kwargs):

    try:
        app_name = sender._meta.app_config.name[:4]
        if app_name not in ('cmj.', 'sapl'):
            return
    except:
        # não é necessário usar logger, aqui é usada apenas para
        # eliminar um o if complexo
        return

    instance = kwargs.get('instance')
    if instance._meta.model in (
        AuditLog,       # Causa recursividade
        # Revisao,        # já é o log de notícias
        ShortRedirect,  # já é o log de redirecionamento de short links
        OcrMyPDF,       # já é o log de execução de ocr
        Bi,              # Bi é um processo automático estatístico
        # Documento
    ):
        return

    logger = logging.getLogger(__name__)

    u = None
    stack = ''
    for i in inspect.stack():
        stack = str(i)
        if i.function == 'migrate':
            return
        r = i.frame.f_locals.get('request', None)
        try:
            if r.user._meta.label == settings.AUTH_USER_MODEL:
                u = r.user
                if u.is_anonymous:
                    return
                break
        except:
            # não é necessário usar logger, aqui é usada apenas para
            # eliminar um o if complexo
            pass

    try:
        # logger.info('\n'.join(stack))

        operation = kwargs.get('operation')
        al = AuditLog()
        al.user = u
        al.email = u.email if u else ''
        al.operation = operation
        al.obj = json.loads(serializers.serialize("json", (instance, )))
        al.content_object = instance if operation != 'D' else None
        al.obj_id = instance.id
        al.model_name = instance._meta.model_name
        al.app_name = instance._meta.app_label

        al.obj[0]['stack'] = stack

        if hasattr(instance, 'visibilidade'):
            al.visibilidade = instance.visibilidade

        al.save()

    except Exception as e:
        logger.error('Error saving auditing log object')
        logger.error(e)


@receiver(post_delete)
def audit_log_post_delete(sender, **kwargs):
    audit_log_function(sender, operation='D', **kwargs)


@receiver(post_save)
def audit_log_post_save(sender, **kwargs):
    operation = 'C' if kwargs.get('created') else 'U'
    audit_log_function(sender, operation=operation, **kwargs)
