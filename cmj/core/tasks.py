import datetime
import logging

from PyPDF4.pdf import PdfFileReader
from asn1crypto import cms
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.signals import post_save, pre_save
from django.utils import timezone
from django.utils.text import slugify
import requests

from cmj.celery import app
from cmj.sigad.models import Documento
from cmj.utils import DisableSignals
from cmj.videos.models import VideoParte
from sapl.materia.models import MateriaLegislativa


logger = logging.getLogger(__name__)

socials_connects = {
    'telegram': dict(
        TOKEN=settings.TELEGRAM_CMJATAI_BOT_KEY,
        API_ID=settings.TELEGRAM_API_ID,
        API_HASH=settings.TELEGRAM_API_HASH,
        CHAT_ID=settings.TELEGRAM_CHAT_ID if not settings.DEBUG else settings.TELEGRAM_CHAT_DEV_ID,
        url_base=f"https://api.telegram.org/bot{settings.TELEGRAM_CMJATAI_BOT_KEY}/{{endpoint}}"
    )
}


@app.task(queue='cq_core', bind=True)
def task_send_rede_social(self, rede, app_label, model_name, pk):
    # print(args)
    # print(kwargs)
    # return

    if 'www' not in settings.SITE_URL:
        return

    send_func = f'send_{rede}_{app_label}_{model_name}'

    #print(f'print, task_send_rede_social iniciou execução: {send_func}')
    logger.info(f'logger task_send_rede_social iniciou execução: {send_func}')

    gf = globals()
    if send_func in gf:
        return gf[send_func](pk)


def send_telegram_sigad_documento(pk):
    #print('send documento iniciou execução')
    logger.info('send documento iniciou execução')

    instance = Documento.objects.filter(pk=pk).first()
    if not instance:
        return

    if 'banco-de-imagens' in instance.slug:
        return

    md = instance.metadata

    if not md:
        md = {}

    if 'send' not in md:
        md['send'] = {}

    md['send']['telegram'] = timezone.localtime()
    instance.metadata = md
    instance.save()

    descricao = instance.descricao or ''
    if descricao and descricao != instance.titulo:
        descricao = f'{chr(10)}{chr(10)}<i>{descricao}</i>'
    else:
        descricao = ''

    texto = instance.texto or ''
    tt = ''
    for t in texto.split(' '):
        if len(tt) < 200:
            tt += t + ' '
        else:
            texto = tt.strip() + '...'
            break
    if texto:
        texto = f"""{chr(10)}{chr(10)}<pre>{texto}</pre>"""

    ct = ContentType.objects.get_by_natural_key('sigad', 'documento')
    vp = VideoParte.objects.filter(
        content_type=ct, object_id=instance.id).first()
    live = ''
    if vp and 'video' in instance.slug:
        link = f'{chr(10)}{chr(10)}https://youtu.be/{vp.video.vid}'
        if vp.video.json['snippet']['liveBroadcastContent'] == 'live':
            live = f'#AoVivo'
    else:
        link = f'{chr(10)}{chr(10)}<a href="{settings.SITE_URL}/{instance.slug}">Leia mais!</a>'

    text = f"""#{instance.classe.titulo} {live}
<b>{instance.titulo}</b>{descricao}{texto}{link}"""

    #<tg-spoiler>spoiler</tg-spoiler>
    # if settings.DEBUG:
    #print(text)
    logger.info(text)
    #    return

    url_base = socials_connects['telegram']['url_base']
    CHAT_ID = socials_connects['telegram']['CHAT_ID']

    try:
        r = requests.post(
            url_base.format(
                endpoint='sendMessage'
            ),
            data={
                'parse_mode': 'html',
                'chat_id': CHAT_ID,
                'text': text,
            }
        )
    except Exception as e:
        logger.error(e)


def send_telegram_materia_materialegislativa(pk):
    #print('send matéria iniciou execução')
    logger.info('send matéria iniciou execução')

    instance = MateriaLegislativa.objects.get(pk=pk)
    md = instance.metadata

    if not md:
        md = {}

    if 'send' not in md:
        md['send'] = {}

    md['send']['telegram'] = timezone.localtime()
    instance.metadata = md
    instance.save()

    autores_hash_tag = ' '.join(
        map(lambda a: '#{}'.format(''.join(str(a.nome).split(' '))), instance.autores.all()))

    autores = '\n'.join(
        map(lambda a: '<i>{}</i>'.format(a), instance.autores.all()))

    text = f"""#{instance.tipo.sigla} #MatériaLegislativa
<b>{str(instance).upper()}</b>

<pre>{instance.ementa}</pre>

Autoria:
{autores}

{autores_hash_tag}
<a href="{settings.SITE_URL}/materia/{instance.id}">Acompanhe o Processo Legislativo desta Matéria clicando aqui.</a>
    """

    #<tg-spoiler>spoiler</tg-spoiler>
    # if settings.DEBUG:
    #print(text)
    logger.info(text)
    #    return

    url_base = socials_connects['telegram']['url_base']
    CHAT_ID = socials_connects['telegram']['CHAT_ID']

    try:
        r = requests.post(
            url_base.format(
                endpoint='sendMessage'
            ),
            data={
                'parse_mode': 'html',
                'chat_id': CHAT_ID,
                'text': text,
            }
        )
        with open(instance.texto_original.path, mode='rb') as fp:

            def custom_filename(item):
                arcname = '{}-{:03d}-{}-{}.{}'.format(
                    item.ano,
                    item.numero,
                    slugify(item.tipo.sigla),
                    slugify(item.tipo.descricao),
                    item.texto_original.path.split('.')[-1])
                return arcname

            r = requests.post(
                url_base.format(
                    endpoint='sendDocument'
                ),
                data={
                    'chat_id': CHAT_ID,
                    'caption': 'Uma cópia na integra do original para você conferir!'
                },
                files={
                    'document': (custom_filename(instance), fp.read(), 'application/pdf')
                }
            )

    except Exception as e:
        logger.error(e)


@app.task(queue='cq_core', bind=True)
def signed_files_extraction(self, app_label, model_name, pk):

    logger.debug(
        f'START signed_files_extraction_post_save_signal {timezone.localtime()}')

    task_signed_files_extraction_function(app_label, model_name, pk)

    logger.debug(
        f'END signed_files_extraction_post_save_signal {timezone.localtime()}')


def task_signed_files_extraction_function(app_label, model_name, pk):

    def run_signed_name_and_date_via_fields(fields):
        signs = {}

        for key, field in fields.items():

            if '/FT' not in field and field['/FT'] != '/Sig':
                continue
            if '/V' not in field:
                continue

            try:
                content_sign = field['/V']['/Contents']
                nome = 'Nome do assinante não localizado.'
                oname = ''
                info = cms.ContentInfo.load(content_sign)
                signed_data = info['content']
                oun_old = []
                for cert in signed_data['certificates']:
                    subject = cert.native['tbs_certificate']['subject']
                    issuer = cert.native['tbs_certificate']['issuer']
                    oname = issuer.get('organization_name', '')

                    if oname in ('Gov-Br', '1Doc'):
                        nome = subject['common_name'].split(':')[0]
                        continue

                    oun = subject['organizational_unit_name']

                    if isinstance(oun, str):
                        continue

                    if len(oun) > len(oun_old):
                        oun_old = oun
                        nome = subject['common_name'].split(':')[0]

                    if oun and isinstance(oun, list) and len(oun) == 4:
                        oname += ' - ' + oun[3]
                        break

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

                    fd = datetime.datetime.strptime(data[2:], '%Y%m%d%H%M%S%z')
            except:
                pass

            if nome and nome not in signs:
                signs[nome] = [fd, oname]

        return list(signs.items())

    def run_signed_name_and_date_extract(file):
        signs = []
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
        fields_br = []
        try:
            pdf = PdfFileReader(file)
            fields = pdf.getFields()
            fields_br = list(
                map(lambda x: x.get('/V', {}).get('/ByteRange', []), fields.values()))
        except Exception as e:
            try:
                pdf = PdfFileReader(file, strict=False)
                fields = pdf.getFields()
                fields_br = list(
                    map(lambda x: x.get('/V', {}).get('/ByteRange', []), fields.values()))
            except Exception as ee:
                fields = ee

        try:
            # se a extração via /Fields ocorrer sem erros e forem capturadas
            # tantas assinaturas quanto byteranges
            if isinstance(fields, dict):
                signs = run_signed_name_and_date_via_fields(fields)
                if len(signs) == len(byterange):
                    return signs

            for n in byterange:

                start = pdfdata.find(b"[", n)
                stop = pdfdata.find(b"]", start)
                assert n != -1 and start != -1 and stop != -1
                n += 1

                br = [int(i, 10) for i in pdfdata[start + 1: stop].split()]

                if br in fields_br:
                    continue

                contents = pdfdata[br[0] + br[1] + 1: br[2] - 1]
                bcontents = bytes.fromhex(contents.decode("utf8"))
                data1 = pdfdata[br[0]: br[0] + br[1]]
                data2 = pdfdata[br[2]: br[2] + br[3]]
                #signedData = data1 + data2

                not_nome = nome = 'Nome do assinante não localizado.'
                oname = ''
                try:
                    info = cms.ContentInfo.load(bcontents)
                    signed_data = info['content']

                    oun_old = []
                    for cert in signed_data['certificates']:
                        subject = cert.native['tbs_certificate']['subject']
                        issuer = cert.native['tbs_certificate']['issuer']
                        oname = issuer.get('organization_name', '')

                        if oname in ('Gov-Br', '1Doc'):
                            nome = subject['common_name'].split(':')[0]
                            continue

                        oun = subject['organizational_unit_name']

                        if isinstance(oun, str):
                            continue

                        if len(oun) > len(oun_old):
                            oun_old = oun
                            nome = subject['common_name'].split(':')[0]

                        if oun and isinstance(oun, list) and len(oun) == 4:
                            oname += ' - ' + oun[3]
                            break

                except Exception as e:
                    pass

                fd = None
                if nome != not_nome:
                    signs.append((nome, [fd, oname]))
        except Exception as e:
            pass

        return signs

    def signed_name_and_date_extract(file):

        try:
            signs = run_signed_name_and_date_extract(file)
        except Exception as e:
            return {}

        data_min = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)

        try:
            signs = sorted(signs, key=lambda sign: (
                sign[0], sign[1][1], sign[1][0] or data_min))
        except Exception as e:
            pass

        signs.reverse()

        signs_dict = {}

        for s in signs:
            if s[0] not in signs_dict or 'ICP' in s[1][1] and 'ICP' not in signs_dict[s[0]][1]:
                signs_dict[s[0]] = s[1]

        signs = sorted(signs_dict.items(), key=lambda sign: (
            sign[0], sign[1][1], sign[1][0]))

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

    model = apps.get_model(app_label, model_name)

    try:
        instance = model.objects.get(pk=pk)
    except:
        return

    if not hasattr(instance, 'FIELDFILE_NAME') or not hasattr(instance, 'metadata'):
        return

    metadata = instance.metadata
    for fn in instance.FIELDFILE_NAME:  # fn -> field_name
        ff = getattr(instance, fn)  # ff -> file_field

        try:
            running_extraction = metadata['signs'][fn]['running_extraction']
        except:
            continue
        else:
            if not running_extraction:
                continue

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
            metadata['signs'][fn] = {}
            logger.error(
                f'Erro ao extrair assinaturas de {instance._meta.concrete_model}: {instance.pk} - {instance}')

    with DisableSignals([pre_save, post_save]):
        try:
            instance.metadata = metadata
            instance.save()
        except:
            logger.error(f'Erro ao salvar {instance.pk} - {instance}')
