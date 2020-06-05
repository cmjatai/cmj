
from django.apps import apps
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail.message import EmailMultiAlternatives
from django.db.models.signals import post_save, pre_save
from django.dispatch.dispatcher import receiver
from django.template import loader
from cmj.core.models import Notificacao
from cmj.settings import EMAIL_SEND_USER
from cmj.utils import signed_name_and_date_extract


def send_mail(subject, email_template_name,
              context, from_email, to_email):

    if settings.DEBUG:
        print('DEBUG: Envio Teste', subject, from_email, to_email)
        return

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
            if not isinstance(ff.file, InMemoryUploadedFile):
                original_absolute_path = '{}/original__{}'.format(
                    ff.storage.location,
                    ff.name)

                with open(original_absolute_path, "rb") as file:
                    meta_signs = signed_name_and_date_extract(
                        file
                    )
                    file.close()
            else:
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
