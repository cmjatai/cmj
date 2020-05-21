from datetime import date, datetime, timedelta
from functools import wraps
import re
from unicodedata import normalize as unicodedata_normalize

from PyPDF4.pdf import PdfFileReader
from asn1crypto import cms
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import connection, models
from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _
from easy_thumbnails import source_generators
from floppyforms import ClearableFileInput
import magic
from model_utils.choices import Choices
from reversion.admin import VersionAdmin
from unipath.path import Path


def pil_image(source, exif_orientation=False, **options):
    return source_generators.pil_image(source, exif_orientation, **options)


def clear_thumbnails_cache(queryset, field, time_create=0):

    now = datetime.now()
    for r in queryset:
        assert hasattr(r, field), _(
            'Objeto da listagem não possui o campo informado')

        if not getattr(r, field):
            continue

        path = Path(getattr(r, field).path)
        cache_files = path.parent.walk()

        for cf in cache_files:
            if cf == path:
                continue

            if time_create:
                data_arquivo = datetime.fromtimestamp(cf.mtime())

                if now - data_arquivo < timedelta(time_create):
                    continue
            cf.remove()


def normalize(txt):
    return unicodedata_normalize(
        'NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


def get_settings_auth_user_model():
    return getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


def register_all_models_in_admin(module_name):
    appname = module_name.split('.')
    appname = appname[1] if appname[0] == 'cmj' else appname[0]
    app = apps.get_app_config(appname)

    for model in app.get_models():
        class CustomModelAdmin(VersionAdmin):
            list_display = [f.name for f in model._meta.fields
                            if f.name != 'id']

        if not admin.site.is_registered(model):
            admin.site.register(model, CustomModelAdmin)


def from_to(start, end):
    return list(range(start, end + 1))


def make_pagination(index, num_pages):
    '''Make a list of adjacent page ranges interspersed with "None"s

    The list starts with [1, 2] and end with [num_pages-1, num_pages].
    The list includes [index-1, index, index+1]
    "None"s separate those ranges and mean ellipsis (...)

    Example:  [1, 2, None, 10, 11, 12, None, 29, 30]
    '''

    PAGINATION_LENGTH = 10
    if num_pages <= PAGINATION_LENGTH:
        return from_to(1, num_pages)
    else:
        if index - 1 <= 5:
            tail = [num_pages - 1, num_pages]
            head = from_to(1, PAGINATION_LENGTH - 3)
        else:
            if index + 1 >= num_pages - 3:
                tail = from_to(index - 1, num_pages)
            else:
                tail = [index - 1, index, index + 1,
                        None, num_pages - 1, num_pages]
            head = from_to(1, PAGINATION_LENGTH - len(tail) - 1)
        return head + [None] + tail


def xstr(s):
    return '' if s is None else str(s)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_base_url(request):
    # TODO substituir por Site.objects.get_current().domain
    # from django.contrib.sites.models import Site

    current_domain = request.get_host()
    protocol = 'https' if request.is_secure() else 'http'
    return "{0}://{1}".format(protocol, current_domain)


def create_barcode(value):
    '''
        creates a base64 encoded barcode PNG image
    '''
    """from base64 import b64encode
    from reportlab.graphics.barcode import createBarcodeDrawing

    barcode = createBarcodeDrawing('Code128',
                                   value=value,
                                   barWidth=170,
                                   height=50,
                                   fontSize=2,
                                   humanReadable=True)
    data = b64encode(barcode.asString('png'))
    return data.decode('utf-8')"""


def CHOICE_SIGNEDS():
    return [('', 'Ambos'),
            (1, 'Documentos Com Assinatura Digital'),
            (0, 'Documentos Sem Assinatura Digital')]


YES_NO_CHOICES = [(True, _('Sim')), (False, _('Não'))]


NONE_YES_NO_CHOICES = [(None, _('---------')),
                       (True, _('Sim')), (False, _('Não'))]


def listify(function):
    @wraps(function)
    def f(*args, **kwargs):
        return list(function(*args, **kwargs))
    return f


UF = [
    ('AC', 'Acre'),
    ('AL', 'Alagoas'),
    ('AP', 'Amapá'),
    ('AM', 'Amazonas'),
    ('BA', 'Bahia'),
    ('CE', 'Ceará'),
    ('DF', 'Distrito Federal'),
    ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'),
    ('MA', 'Maranhão'),
    ('MT', 'Mato Grosso'),
    ('MS', 'Mato Grosso do Sul'),
    ('MG', 'Minas Gerais'),
    ('PR', 'Paraná'),
    ('PB', 'Paraíba'),
    ('PA', 'Pará'),
    ('PE', 'Pernambuco'),
    ('PI', 'Piauí'),
    ('RJ', 'Rio de Janeiro'),
    ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'),
    ('RO', 'Rondônia'),
    ('RR', 'Roraima'),
    ('SC', 'Santa Catarina'),
    ('SE', 'Sergipe'),
    ('SP', 'São Paulo'),
    ('TO', 'Tocantins'),
    ('EX', 'Exterior'),
]

RANGE_ANOS = [(year, year) for year in range(date.today().year, 1889, -1)]

RANGE_MESES = [
    (1, 'Janeiro'),
    (2, 'Fevereiro'),
    (3, 'Março'),
    (4, 'Abril'),
    (5, 'Maio'),
    (6, 'Junho'),
    (7, 'Julho'),
    (8, 'Agosto'),
    (9, 'Setembro'),
    (10, 'Outubro'),
    (11, 'Novembro'),
    (12, 'Dezembro'),
]

RANGE_DIAS_MES = [(n, n) for n in range(1, 32)]


TIPOS_MIDIAS_PERMITIDOS = {
    'application/pdf': 'pdf',
    'application/x-pdf': 'pdf',
    'application/acrobat': 'pdf',
    'applications/vnd.pdf': 'pdf',
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/jpe_': 'jpg',
    'image/pjpeg': 'jpg',
    'image/vnd.swiftview-jpeg': 'jpg',
    'application/jpg': 'jpg',
    'application/x-jpg': 'jpg',
    'image/pjpeg': 'jpg',
    'image/pipeg': 'jpg',
    'image/vnd.swiftview-jpeg': 'jpg',
    'image/gif': 'gif',
    'image/png': 'png',
    'application/png': 'png',
    'application/x-png': 'png',
}

TIPOS_IMG_PERMITIDOS = {
    'image/jpeg',
    'image/jpg',
    'image/jpe_',
    'image/pjpeg',
    'image/vnd.swiftview-jpeg',
    'application/jpg',
    'application/x-jpg',
    'image/pjpeg',
    'image/pipeg',
    'image/vnd.swiftview-jpeg',
    'image/x-xbitmap',
    'image/bmp',
    'image/x-bmp',
    'image/x-bitmap',
    'image/png',
    'application/png',
    'application/x-png'
}


def fabrica_validador_de_tipos_de_arquivo(lista, nome):

    def restringe_tipos_de_arquivo(value):
        mime = magic.from_buffer(value.read(), mime=True)
        if mime not in lista:
            raise ValidationError(_('Tipo de arquivo não suportado'))
        return mime, lista[mime]
    # o nome é importante para as migrations
    restringe_tipos_de_arquivo.__name__ = nome
    return restringe_tipos_de_arquivo


restringe_tipos_de_arquivo_midias = fabrica_validador_de_tipos_de_arquivo(
    TIPOS_MIDIAS_PERMITIDOS, 'restringe_tipos_de_arquivo_midias')


def intervalos_tem_intersecao(a_inicio, a_fim, b_inicio, b_fim):
    maior_inicio = max(a_inicio, b_inicio)
    menor_fim = min(a_fim, b_fim)
    return maior_inicio <= menor_fim


media_protected_storage = FileSystemStorage(
    location=settings.MEDIA_PROTECTED_ROOT, base_url='DO_NOT_USE')


def texto_upload_path(instance, filename, subpath='', pk_first=False):

    filename = re.sub('\s', '_', normalize(filename.strip()).lower())

    prefix = 'public'

    str_path = ('./cmj/%(prefix)s/%(model_name)s/'
                '%(subpath)s/%(pk)s/%(filename)s')

    if pk_first:
        str_path = ('./cmj/%(prefix)s/%(model_name)s/'
                    '%(pk)s/%(subpath)s/%(filename)s')

    if subpath is None:
        subpath = '_'

    path = str_path % \
        {
            'prefix': prefix,
            'model_name': instance._meta.model_name,
            'pk': instance.pk,
            'subpath': subpath,
            'filename': filename
        }

    return path


def run_sql(sql):
    with connection.cursor() as cursor:

        cursor.execute(sql)

        if sql.startswith('select'):
            rows = cursor.fetchall()

            if settings.DEBUG:
                print(rows)


def signed_name_and_date_extract(file):
    signs = []
    try:
        pdf = PdfFileReader(file)
    except Exception as e:
        try:
            pdf = PdfFileReader(file, strict=False)
        except Exception as ee:
            return signs

    fields = pdf.getFields()

    if not fields:
        return signs

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
        signs.append((nome, fd))
    return signs
