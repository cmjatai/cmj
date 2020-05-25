
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from cmj.core.signals import send_mail
from cmj.settings import EMAIL_SEND_USER
from sapl.protocoloadm.models import Protocolo


@receiver(post_save, sender=Protocolo, dispatch_uid='protocolo_post_save')
def protocolo_post_save(sender, instance, using, **kwargs):

    import inspect
    funcs = list(filter(lambda x: x == 'revision_pre_delete_signal',
                        map(lambda x: x[3], inspect.stack())))

    if funcs:
        return

    if hasattr(instance, 'not_send_mail') and instance.not_send_mail:
        return
    try:

        if instance.email:
            send_mail(
                instance.epigrafe,
                'email/comprovante_protocolo.html',
                {'protocolo': instance}, EMAIL_SEND_USER, 'leandro@jatai.go.leg.br')  # instance.email)

            print('Um Email com comprovante de protocolo foi enviado '
                  '%s - user: %s - user_origin: %s' % (
                      instance.pk,
                      instance.email,
                      instance.interessado))
    except:
        pass
