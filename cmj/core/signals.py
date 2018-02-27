from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from cmj.core.models import Notificacao


@receiver(post_save, sender=Notificacao, dispatch_uid='notificacao_post_save')
def notificacao_post_save(sender, instance, using, **kwargs):

    print('Uma Notificação foi enviada %s - user: %s - user_origin: %s' % (
        instance.pk,
        instance.user,
        instance.user_origin))
