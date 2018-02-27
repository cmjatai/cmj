from django.core.mail.message import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.template import loader
from django.utils.encoding import force_text

from cmj.core.models import Notificacao
from cmj.settings import EMAIL_SEND_USER


def send_mail(subject, email_template_name,
              context, from_email, to_email):

    subject = ''.join(subject.splitlines())

    html_email = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, '', from_email, [to_email])
    email_message.attach_alternative(html_email, 'text/html')
    email_message.send()


@receiver(post_save, sender=Notificacao, dispatch_uid='notificacao_post_save')
def notificacao_post_save(sender, instance, using, **kwargs):

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
