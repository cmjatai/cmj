from datetime import datetime
import inspect
import json
import logging

from PyPDF4.pdf import PdfFileReader
from asn1crypto import cms
from django.conf import settings
from django.core import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail.message import EmailMultiAlternatives
from django.template import loader
from django.utils import timezone

from cmj.core.models import AuditLog, OcrMyPDF, Bi
from cmj.sigad.models import ShortRedirect


def send_mail(subject, email_template_name,
              context, from_email, to_email):
    subject = ''.join(subject.splitlines())

    html_email = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, '', from_email, [to_email])
    email_message.attach_alternative(html_email, 'text/html')
    email_message.send()


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


def signed_name_and_date_extract_pre_save(sender, instance, using, **kwargs):
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
