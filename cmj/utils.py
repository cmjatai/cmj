from collections import defaultdict
from datetime import date, datetime, timedelta
from functools import wraps
from unicodedata import normalize as unicodedata_normalize
import logging
import re
import ssl
import subprocess
import threading

from crispy_forms.bootstrap import Alert
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.mail.backends.smtp import EmailBackend
from django.db import connection
from django.db.models import Q
from django.db.models.signals import pre_init, post_init, pre_save, post_save, \
    pre_delete, post_delete, post_migrate, pre_migrate, m2m_changed
from django.template.loaders.filesystem import Loader
from django.urls.base import resolve
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _
from easy_thumbnails import source_generators
from unipath.path import Path
from weasyprint import HTML
import magic

from cmj.celery import app as celery_app


media_protected_storage = FileSystemStorage(
    location=settings.MEDIA_PROTECTED_ROOT, base_url='DO_NOT_USE')


media_cache_storage = FileSystemStorage(
    location=settings.MEDIA_CACHE_ROOT, base_url='DO_NOT_USE')


def get_celery_worker_status():
    i = celery_app.control.inspect()
    availability = i.ping()
    stats = i.stats()
    registered_tasks = i.registered()
    active_tasks = i.active()
    scheduled_tasks = i.scheduled()
    result = {
        'availability': availability,
        'stats': stats,
        'registered_tasks': registered_tasks,
        'active_tasks': active_tasks,
        'scheduled_tasks': scheduled_tasks
    }
    return result


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


def clean_text(text, _normalizes=None):
    txt = text
    try:
        normalizes = _normalizes or (
            (r'\n ?\d+ ?/ ?\d+ ?\n', '\n'),
            (r'[ ]{2,}', ' '),
            (r' \n', '\n'),
            #('([^\.]|\S)\n(\S)', r'\1 \2'),
            (r'(\w)\n(.)', r'\1 \2'),
            (r'(,|\.)\n(.)', r'\1 \2'),
            #('()\n()', r'\1 \2'),
            (r'\n\n', '\n'),
            (r'-\n', '-'),
            (r'^\n', ''),
            ('–', '-'),
            ('•', '*'),
            ('[“”]', '"'),
            #('', ''),
            #('', ''),
            #('', ''),
            #('', ''),
            #('', ''),
        )

        for regex, new in normalizes:
            search = re.search(regex, text)
            while search:
                text = re.sub(regex, new, text)
                search = re.search(regex, text)
        return text
    except:
        return txt


def get_settings_auth_user_model():
    return getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


def register_all_models_in_admin(module_name):
    appname = module_name.split('.')
    appname = appname[1] if appname[0] == 'cmj' else appname[0]
    app = apps.get_app_config(appname)

    for model in app.get_models():
        if not admin.site.is_registered(model):
            admin.site.register(model)


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
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/vnd.oasis.opendocument.text': 'odt',

    'application/vnd.ms-excel': 'xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.oasis.opendocument.spreadsheet': 'ods',

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
    'image/tiff': 'tiff'
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


def texto_upload_path(instance, filename, subpath='', pk_first=False, _prefix='public'):

    filename = re.sub(r'\s', '_', normalize(filename.strip()).lower())

    prefix = _prefix

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


def period2dict(period):

    ISO8601_PERIOD_REGEX = re.compile(
        r"^(?P<sign>[+-])?"
        r"P(?!\b)"
        r"(?P<years>[0-9]+Y)?"
        r"(?P<months>[0-9]+M)?"
        r"(?P<weeks>[0-9]+W)?"
        r"(?P<days>[0-9]+D)?"
        r"((?P<separator>T)(?P<hours>[0-9]+H)?"
        r"(?P<minutes>[0-9]+M)?"
        r"(?P<seconds>[0-9]+S)?)?$")

    m = ISO8601_PERIOD_REGEX.match(period)
    if not m:
        return {}
    groups = m.groupdict()

    for k, v in groups.items():
        if k not in ('separator', 'sign'):
            if v is None:
                groups[k] = "0n"
            groups[k] = int(groups[k][:-1])
    return groups


def time_of_period(period):

    pd = period2dict(period)

    if not pd:
        return ''

    pd['hours'] = int(pd['hours']) if pd['hours'] else 0

    pd['hours'] += int(pd['years']) * \
        8760 if 'years' in pd and pd['years'] else 0

    pd['hours'] += int(pd['months']) * \
        720 if 'months' in pd and pd['months'] else 0

    pd['hours'] += int(pd['weeks']) * \
        168 if 'weeks' in pd and pd['weeks'] else 0

    pd['hours'] += int(pd['days']) * \
        24 if 'days' in pd and pd['days'] else 0

    r = '{hours}{separator1}{minutes:02d}:{seconds:02d}'.format(
        hours=pd['hours'] if pd['hours'] else '',
        separator1=':' if pd['hours'] else '',
        minutes=pd['minutes'],
        seconds=pd['seconds'],
    )
    seconds = pd['hours'] * 3600 + pd['minutes'] * 60 + pd['seconds']
    return r, seconds


def run_sql(sql):
    result = []
    with connection.cursor() as cursor:

        result = cursor.execute(sql)

        if sql.lower().startswith('select'):
            result = cursor.fetchall()

    return result

    # if settings.DEBUG:
    #    print(rows)


def make_pdf(base_url,
             main_template,
             header_template='',
             footer_template='',
             main_css='',
             header_css=''
             ):

    html = HTML(base_url=base_url, string=main_template)

    main_doc = html.render(stylesheets=[])

    def get_page_body(boxes):
        for box in boxes:
            if box.element_tag == 'body':
                return box
            return get_page_body(box.all_children())

    if header_template:
        html = HTML(base_url=base_url, string=header_template)
        header = html.render(
            stylesheets=[])

        header_page = header.pages[0]
        header_body = get_page_body(header_page._page_box.all_children())
        header_body = header_body.copy_with_children(
            header_body.all_children())

    if footer_template:
        html = HTML(base_url=base_url, string=footer_template)
        footer = html.render(
            stylesheets=[])

        footer_page = footer.pages[0]
        footer_body = get_page_body(footer_page._page_box.all_children())
        footer_body = footer_body.copy_with_children(
            footer_body.all_children())

    for page in main_doc.pages:

        page_body = get_page_body(page._page_box.all_children())

        if header_template:
            page_body.children += header_body.all_children()

        if footer_template:
            page_body.children += footer_body.all_children()

    pdf_file = main_doc.write_pdf()
    main_doc

    return pdf_file


def get_breadcrumb_classes(context, request=None, response=None):

    if not context or not request or request.path == '/':
        return response

    from cmj.sigad.models import Documento, Classe

    obj = context.get('object', None)

    if obj and (isinstance(obj, Classe) or isinstance(obj, Documento)):
        context.update(
            {
                'title': obj,
                'breadcrumb_classes': obj.classes_parents_and_me
            })
        return response

    path = request.path
    fpath = request.get_full_path()

    paths = []
    try:
        resolve_match = resolve(path)
        view_name = str(resolve_match.view_name)
    except:
        view_name = ''
    else:
        paths.append(view_name)

    paths.append(fpath)
    if path != paths[-1]:
        paths.append(path)

    for i, path in enumerate(paths):
        q = Q(url_redirect=path) | Q(slug=path[1:])
        classe_redirect = Classe.objects.filter(q).first()
        if classe_redirect:
            breads = classe_redirect.classes_parents_and_me
            if obj:
                breads.extend([obj])
            context.update({'breadcrumb_classes': breads})
            if not obj and path != view_name:
                context.update({
                    'title': classe_redirect
                })
            return response

    documento = Documento.objects.filter(slug=path[1:]).first()
    if documento:
        context.update(
            {
                'title': documento,
                'breadcrumb_classes': documento.classes_parents_and_me
            })
        return response

    return response


class ProcessoExterno(object):

    returncode = None
    stdout = None
    stderr = None

    def __init__(self, cmd, logger):
        self.cmd = cmd
        self.process = None
        self.logger = logger

    def run(self, timeout):

        def target():
            self.logger.info('Thread started')
            self.process = subprocess.Popen(
                self.cmd,
                shell=True,
                stdout=subprocess.PIPE)
            self.stdout, self.stderr = self.process.communicate()
            self.returncode = self.process.returncode
            self.logger.info(self.returncode)
            self.logger.info(self.stdout)
            self.logger.info(self.stderr)
            self.logger.info('Thread finished:')

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.logger.info('Killed process')
            self.process.kill()
            return None
            # thread.join()

        return self.returncode, self.stdout, self.stderr


#logger = logging.getLogger(__name__)
#cmd = "ls -la"
#p = ProcessoExterno(cmd, logger)
#r = p.run(60)


class CmjLoader(Loader):

    def get_dirs(self):
        return self.dirs if self.dirs is not None else self.engine.dirs


class Manutencao(object):

    def desativa_signals(self, app_signal=None):

        disabled_signals = [
            pre_init, post_init,
            pre_save, post_save,
            pre_delete, post_delete,
            pre_migrate, post_migrate,
            m2m_changed
        ]
        for s in disabled_signals:
            for r in s.receivers:
                continue
                print(r)
            s.receivers = []

        return

        for app in apps.get_app_configs():
            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():
                for s in disabled_signals:
                    rs = s._live_receivers(m)
                    if rs:
                        for r in rs:
                            if s.disconnect(receiver=r, sender=m):
                                print(m, s, r)

    def desativa_auto_now(self):
        from cmj.core.models import AuditLog
        for app in apps.get_app_configs():

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():
                if m == AuditLog:
                    continue

                for f in m._meta.get_fields():
                    dua = f
                    # print(dua)

                    if hasattr(dua, 'auto_now'):
                        dua._auto_now = dua.auto_now
                        dua.auto_now = False

                    if hasattr(dua, 'auto_now_add'):
                        dua._auto_now_add = dua.auto_now_add
                        dua.auto_now_add = False

    def ativa_auto_now(self):
        from cmj.core.models import AuditLog
        for app in apps.get_app_configs():

            if not app.name.startswith('cmj') and not app.name.startswith('sapl'):
                continue

            for m in app.get_models():
                if m == AuditLog:
                    continue

                for f in m._meta.get_fields():
                    dua = f
                    # print(dua)

                    if hasattr(dua, '_auto_now'):
                        dua.auto_now = dua._auto_now

                    if hasattr(dua, '_auto_now_add'):
                        dua.auto_now_add = dua._auto_now_add


class DisableSignals(object):
    def __init__(self, disabled_signals=None):
        self.stashed_signals = defaultdict(list)
        self.disabled_signals = disabled_signals or [
            pre_init, post_init,
            pre_save, post_save,
            pre_delete, post_delete,
            pre_migrate, post_migrate,
            m2m_changed
        ]

    def __enter__(self):
        for signal in self.disabled_signals:
            self.disconnect(signal)

    def __exit__(self, exc_type, exc_val, exc_tb):
        keys = list(self.stashed_signals.keys())
        for signal in keys:
            self.reconnect(signal)

    def disconnect(self, signal):
        self.stashed_signals[signal] = signal.receivers
        signal.receivers = []

    def reconnect(self, signal):
        signal.receivers = self.stashed_signals.get(signal, [])
        del self.stashed_signals[signal]
        signal.sender_receivers_cache.clear()


class TimeExecution(object):
    def __init__(self, print_date=False):
        self.print_date = print_date

    def __enter__(self):
        self.start = timezone.localtime()
        if self.print_date:
            print(self.start)

    def __exit__(self, exc_type, exc_val, exc_tb):
        end = timezone.localtime()
        if self.print_date:
            print(end)
        print('TimeExecution:', end - self.start)


class CmjEmailBackend(EmailBackend):

    @cached_property
    def ssl_context(self):
        if self.ssl_certfile or self.ssl_keyfile:
            ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
            ssl_context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
            return ssl_context
        else:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode


class AlertSafe(Alert):

    def __init__(self, content, dismiss=True, block=False, css_id=None, css_class=None, template=None, **kwargs):
        super().__init__(SafeString(content), dismiss,
                         block, css_id, css_class, template, **kwargs)
