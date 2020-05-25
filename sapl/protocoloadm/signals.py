from django.db.models.signals import post_save, pre_save
from django.dispatch.dispatcher import receiver

from cmj.core.signals import send_mail
from cmj.settings import EMAIL_SEND_USER
from sapl.protocoloadm.models import Protocolo
from sapl.utils import create_barcode


@receiver(pre_save, sender=Protocolo, dispatch_uid='protocolo_pre_save')
def protocolo_pre_save(sender, instance, using, **kwargs):

    import inspect
    funcs = list(filter(lambda x: x == 'revision_pre_delete_signal',
                        map(lambda x: x[3], inspect.stack())))

    if funcs:
        return

    if hasattr(instance, 'not_send_mail') and instance.not_send_mail:
        return
    try:

        if instance.email:

            if instance.timestamp:
                data = instance.timestamp.strftime("%Y/%m/%d")
            else:
                data = instance.data.strftime("%Y/%m/%d")

            base64_data = create_barcode(str(instance.numero).zfill(6))
            barcode = 'data:image/png;base64,{0}'.format(base64_data)
            autenticacao = str(instance.tipo_processo) + \
                data + str(instance.numero).zfill(6)

            send_mail(
                'Protocolo: {}'.format(instance.epigrafe),
                'email/comprovante_protocolo.html',
                {'protocolo': instance,
                    'barcode': barcode,
                    'autenticacao': autenticacao}, EMAIL_SEND_USER, 'leandro@jatai.go.leg.br')  # instance.email)

            print('Um Email com comprovante de protocolo foi enviado '
                  '%s - email: %s - interessado: %s' % (
                      instance.pk,
                      instance.email,
                      instance.interessado))
            instance.comprovante_automatico_enviado = True
    except Exception as e:
        print(e)
        pass
