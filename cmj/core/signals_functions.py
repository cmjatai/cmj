from datetime import datetime, date, timedelta
import inspect
import json
import logging

from PyPDF4.pdf import PdfFileReader
from asgiref.sync import async_to_sync
from asn1crypto import cms
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail.message import EmailMultiAlternatives
from django.template import loader
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from cmj.core import tasks
from cmj.core.models import AuditLog, OcrMyPDF, Bi
from cmj.settings.email import EMAIL_SEND_USER
from cmj.sigad.models import ShortRedirect
from cmj.videos.models import VideoParte


logger = logging.getLogger(__name__)


def auditlog_signal_function(sender, **kwargs):

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

        operation = kwargs.get('created', 'D')
        if operation != 'D':
            operation = 'C' if operation else 'U'

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


def notificacao_signal_function(sender, instance, **kwargs):

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


def redesocial_post_function_time_call_documento(inst):
    if settings.DEBUG:
        return 30
    ct = ContentType.objects.get_by_natural_key('sigad', 'documento')
    vp = VideoParte.objects.filter(
        content_type=ct, object_id=inst.id).first()

    if inst.classe_id in (10, ):
        raise Exception

    if not vp:
        return 3600

    if vp.video.json['snippet']['liveBroadcastContent'] == 'live':
        return 120
    elif vp.video.json['snippet']['liveBroadcastContent'] == 'none':
        return 3600
    raise Exception


def redesocial_post_function_time_call_materialegislativa(inst):
    if settings.DEBUG:
        return 30
    return 600


def redesocial_post_function(sender, instance, **kwargs):

    return

    if not hasattr(instance, '_meta') or \
        instance._meta.app_config is None or \
            not instance._meta.app_config.name in settings.BUSINESS_APPS:
        return

    if not hasattr(instance, 'metadata'):
        return

    if hasattr(instance, 'parent') and instance.parent:
        return

    running = {
        'MateriaLegislativa': {
            'data_min': date(2022, 9, 7) if not settings.DEBUG else date(2022, 1, 1),
            'time_call': redesocial_post_function_time_call_materialegislativa
        },
        'Documento': {
            'data_min': date(2022, 9, 11) if not settings.DEBUG else date(2022, 1, 1),
            'time_call': redesocial_post_function_time_call_documento
        },
    }

    if instance._meta.object_name not in running.keys():
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

                if d < running[instance._meta.object_name]['data_min']:
                    return

        now = timezone.now()
        try:
            td = timedelta(
                seconds=running[instance._meta.object_name]['time_call'](
                    instance)
            )
        except:
            return

        s[r] = timezone.localtime()
        md['send'] = s
        instance.metadata = md
        instance.save()

        print('chamou task_send_rede_social', td)
        logger.info('chamou task_send_rede_social')
        tasks.task_send_rede_social.apply_async(
            (
                r,
                instance._meta.app_label,
                instance._meta.model_name,
                instance.id
            ),
            eta=now + td
        )


def send_mail(subject, email_template_name, context, from_email, to_email):
    subject = ''.join(subject.splitlines())
    html_email = loader.render_to_string(email_template_name, context)
    email_message = EmailMultiAlternatives(subject, '', from_email, [to_email])
    email_message.attach_alternative(html_email, 'text/html')
    email_message.send()


def send_signal_for_websocket_time_refresh(inst, **kwargs):

    action = 'post_save' if 'created' in kwargs else 'post_delete'

    if hasattr(inst, '_meta') and \
        not inst._meta.app_config is None and \
            inst._meta.app_config.name[:4] in ('sapl', ):  # 'cmj.'):

        try:
            if hasattr(inst, 'ws_sync') and not inst.ws_sync():
                return

            channel_layer = get_channel_layer()

            async_to_sync(channel_layer.group_send)(
                "group_time_refresh_channel", {
                    "type": "time_refresh.message",
                    'message': {
                        'action': action,
                        'id': inst.id,
                        'app': inst._meta.app_label,
                        'model': inst._meta.model_name
                    }
                }
            )
        except Exception as e:
            logger.info(_("Erro na comunicação com o backend do redis. "
                          "Certifique se possuir um servidor de redis "
                          "ativo funcionando como configurado em "
                          "CHANNEL_LAYERS"))


def signed_files_extraction_function(sender, instance, **kwargs):

    def run_signed_name_and_date_via_fields(fields):
        signs = {}

        for key, field in fields.items():

            if '/FT' not in field and field['/FT'] != '/Sig':
                continue
            if '/V' not in field:
                continue

                # .format(field['/V']['/Reason'])
            nome = 'Nome do assinante não localizado.'
            content_sign = field['/V']['/Contents']
            try:
                signed_data = cms.ContentInfo.load(content_sign)['content']
                oun_old = []
                for cert in signed_data['certificates']:
                    subject = cert.native['tbs_certificate']['subject']
                    oun = subject['organizational_unit_name']

                    if isinstance(oun, str):
                        continue

                    if len(oun) > len(oun_old):
                        oun_old = oun
                        nome = subject['common_name'].split(':')[0]
            except:
                if '/Name' in field['/V']:
                    nome = field['/V']['/Name']

            fd = None
            try:
                data = str(field['/V']['/M'])

                if 'D:' not in data:
                    data = None
                else:
                    if not data.endswith('Z'):
                        data = data.replace('Z', '+')
                    data = data.replace("'", '')

                    fd = datetime.strptime(data[2:], '%Y%m%d%H%M%S%z')
            except:
                pass

            if nome not in signs:
                signs[nome] = fd

        return signs

    def run_signed_name_and_date_extract(file):
        signs = {}
        fields = {}
        pdfdata = file.read()

        # se não tem byterange então não é assinado
        byterange = []
        n = -1
        while True:
            n = pdfdata.find(b"/ByteRange", n + 1)
            if n == -1:
                break
            byterange.append(n)

        if not byterange:
            return signs

        # tenta extrair via /Fields
        try:
            pdf = PdfFileReader(file)
            fields = pdf.getFields()
        except Exception as e:
            try:
                pdf = PdfFileReader(file, strict=False)
                fields = pdf.getFields()
            except Exception as ee:
                fields = ee

        try:
            # se a extração via /Fields ocorrer sem erros e forem capturadas
            # tantas assinaturas quanto byteranges
            if isinstance(fields, dict):
                signs = run_signed_name_and_date_via_fields(fields)
                if len(signs) == len(byterange):
                    return signs
        except Exception as e:
            pass

        try:
            for n in byterange:

                start = pdfdata.find(b"[", n)
                stop = pdfdata.find(b"]", start)
                assert n != -1 and start != -1 and stop != -1
                n += 1

                br = [int(i, 10) for i in pdfdata[start + 1: stop].split()]
                contents = pdfdata[br[0] + br[1] + 1: br[2] - 1]
                bcontents = bytes.fromhex(contents.decode("utf8"))
                data1 = pdfdata[br[0]: br[0] + br[1]]
                data2 = pdfdata[br[2]: br[2] + br[3]]
                #signedData = data1 + data2

                nome = 'Nome do assinante não localizado.'
                try:
                    signed_data = cms.ContentInfo.load(bcontents)['content']
                    oun_old = []
                    for cert in signed_data['certificates']:
                        subject = cert.native['tbs_certificate']['subject']
                        oun = subject['organizational_unit_name']

                        if isinstance(oun, str):
                            continue

                        if len(oun) > len(oun_old):
                            oun_old = oun
                            nome = subject['common_name'].split(':')[0]

                        if nome not in signs:
                            signs[nome] = timezone.localtime()
                except Exception as e:
                    pass
        except Exception as e:
            pass

        return signs

    def signed_name_and_date_extract(file):

        try:
            signs = run_signed_name_and_date_extract(file)
        except Exception as e:
            return {}

        signs = list(signs.items())
        signs = sorted(signs, key=lambda sign: sign[0])

        sr = []

        for s in signs:
            tt = s[0].title().split(' ')
            for idx, t in enumerate(tt):
                if t in ('Dos', 'De', 'Da', 'Do', 'Das', 'E'):
                    tt[idx] = t.lower()
            sr.append((' '.join(tt), s[1]))

        signs = sr

        meta_signs = {
            'signs': [],
            'hom': []
        }

        for s in signs:
            cn = settings.CERT_PRIVATE_KEY_NAME
            meta_signs['hom' if s[0] == cn else 'signs'].append(s)
        return meta_signs

    # checa se documento está homologado

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
