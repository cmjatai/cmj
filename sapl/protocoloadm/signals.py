import logging

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch.dispatcher import receiver

from cmj.core.signals_functions import send_mail
from cmj.settings import EMAIL_SEND_USER
from sapl.protocoloadm.models import Protocolo, DocumentoAdministrativo
from sapl.utils import create_barcode


logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Protocolo, dispatch_uid='protocolo_pre_save')
def protocolo_pre_save(sender, instance, using, **kwargs):

    if hasattr(instance, 'not_send_mail') and instance.not_send_mail:
        return
    if instance.email and instance.conteudo_protocolado:
        try:
            if instance.timestamp:
                data = instance.timestamp.strftime("%Y/%m/%d")
            else:
                data = instance.data.strftime("%Y/%m/%d")

            base64_data = create_barcode(str(instance.numero).zfill(6))
            barcode = 'data:image/png;base64,{0}'.format(base64_data)
            autenticacao = str(instance.tipo_processo) + \
                data + str(instance.numero).zfill(6)

            if not settings.DEBUG:
                send_mail(
                    'Protocolo: {}'.format(instance.epigrafe),
                    'email/comprovante_protocolo.html',
                    {'protocolo': instance,
                        'barcode': barcode,
                        'autenticacao': autenticacao}, EMAIL_SEND_USER, instance.email)  # 'leandro@jatai.go.leg.br')  #
            else:
                send_mail(
                    'Protocolo: {}'.format(instance.epigrafe),
                    'email/comprovante_protocolo.html',
                    {'protocolo': instance,
                        'barcode': barcode,
                        'autenticacao': autenticacao}, EMAIL_SEND_USER, 'leandro@jatai.go.leg.br')  #

            logger.info(
                'Um Email com comprovante de protocolo foi enviado '
                '%s - email: %s - interessado: %s' % (
                    instance.pk,
                    instance.email,
                    instance.interessado))

            instance.comprovante_automatico_enviado = True
        except Exception as e:
            logger.error(
                """
                Erro no envio de email de comprovante de protocolo.
                para: {}
                {}
                {}
                --------------------
                {}
                """.format(
                    instance.email,
                    instance,
                    instance.conteudo_protocolado,
                    e

                ))


@receiver(pre_save, sender=DocumentoAdministrativo, dispatch_uid='docadm_pre_save_segmenta_download')
def docadm_pre_save_segmenta_download(sender, instance, using, **kwargs):

    if not instance.id:
        return

    md = instance.metadata if instance.metadata else {}

    # print(md)

    md['zipfile'] = {}

    zf = md['zipfile']

    zip_num = 1
    zip_size = 0

    zf['{:03d}'.format(zip_num)] = {
        'da': [],
        'daa': [],
        'ml': [],
    }
    counts = {
        'zn': 1,
        'zs': 0
    }

    def tree_add_files(nd, zf, cc):

        key = '{:03d}'.format(cc['zn'])

        if hasattr(nd, 'texto_integral'):
            if nd.texto_integral:

                if cc['zs'] > (1024 ** 3) or (
                        cc['zs'] + nd.texto_integral.size > (1024 ** 3) * 2):
                    # se já é maior que 1GB ou ao adicionar um arquivo fique
                    # maior 2GB
                    cc['zn'] += 1
                    key = '{:03d}'.format(cc['zn'])
                    cc['zs'] = 0
                    zf[key] = {
                        'da': [],
                        'daa': [],
                        'ml': [],
                    }

                cc['zs'] += nd.texto_integral.size
                zf[key]['da'].append(nd.id)

            for da in nd.anexados.order_by('id'):
                tree_add_files(da, zf, cc)

            for daa in nd.documentoacessorioadministrativo_set.all():
                tree_add_files(daa, zf, cc)

            if hasattr(nd, 'materia') and nd.materia:
                tree_add_files(nd.materia, zf, cc)

        elif hasattr(nd, 'arquivo'):
            if nd.arquivo:

                if cc['zs'] > (1024 ** 3) or (
                        cc['zs'] + nd.arquivo.size > (1024 ** 3) * 2):
                    # se já é maior que 1GB ou ao adicionar um arquivo fique
                    # maior 2GB
                    cc['zn'] += 1
                    key = '{:03d}'.format(cc['zn'])
                    cc['zs'] = 0
                    zf[key] = {
                        'da': [],
                        'daa': [],
                        'ml': [],
                    }

                cc['zs'] += nd.arquivo.size
                zf[key]['daa'].append(nd.id)

        elif hasattr(nd, 'texto_original'):
            if nd.texto_original:

                if cc['zs'] > (1024 ** 3) or (
                        cc['zs'] + nd.texto_original.size > (1024 ** 3) * 2):
                    # se já é maior que 1GB ou ao adicionar um arquivo fique
                    # maior 2GB
                    cc['zn'] += 1
                    key = '{:03d}'.format(cc['zn'])
                    cc['zs'] = 0
                    zf[key] = {
                        'da': [],
                        'daa': [],
                        'ml': [],
                    }

                cc['zs'] += nd.texto_original.size
                zf[key]['ml'].append(nd.id)

    tree_add_files(instance, zf, counts)
    instance.metadata = md
