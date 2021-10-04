
from datetime import date, timedelta
import json

from dateutil.relativedelta import relativedelta
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.template.defaultfilters import stringfilter
from django.utils import timezone
from django.utils.dateparse import parse_datetime as django_parse_datetime
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from webpack_loader import utils
from webpack_loader.utils import _get_bundle

from sapl.base.models import AppConfig
from sapl.materia.models import TipoMateriaLegislativa
from sapl.norma.models import NormaJuridica, TipoNormaJuridica
from sapl.parlamentares.models import Filiacao
from sapl.sessao.models import SessaoPlenaria

register = template.Library()


@register.filter('startswith')
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter('jsonify')
def jsonify(object):
    if isinstance(object, QuerySet):
        return mark_safe(serialize('json', object))
    return mark_safe(json.dumps(object))


@register.filter('to_dict')
def to_dict(object):
    return object.__dict__


@register.filter
def sessao_em_andamento(obj):
    sps = SessaoPlenaria.objects.order_by('-id')
    for sp in sps:
        if not sp.legislatura.atual():
            continue

        if sp.iniciada and not sp.finalizada:
            return True

    return False


def get_class(class_string):
    if not hasattr(class_string, '__bases__'):
        class_string = str(class_string)
        dot = class_string.rindex('.')
        mod_name, class_name = class_string[:dot], class_string[dot + 1:]

        try:
            ct = ContentType.objects.get_by_natural_key(
                mod_name, class_name.lower())
            if ct:
                return ct.model_class()
            return None
        except:
            if class_name:
                return getattr(__import__(mod_name, {}, {}, [str('')]), class_name)
            return None


@register.simple_tag
def field_verbose_name(instance, field_name):
    return instance._meta.get_field(field_name).verbose_name


@register.simple_tag
def fieldclass_verbose_name(class_name, field_name):
    cls = get_class(class_name)
    return cls._meta.get_field(field_name).verbose_name


@register.simple_tag
def model_verbose_name(class_name):
    model = get_class(class_name)
    return model._meta.verbose_name


@register.simple_tag
def model_verbose_name_plural(class_name):
    model = get_class(class_name)
    if model:
        return model._meta.verbose_name_plural
    return ''


@register.filter
def meta_model_value(instance, attr):
    try:
        return getattr(instance._meta, attr)
    except:
        return ''


@register.filter
def lookup(d, key):
    return d[key] if key in d else []


@register.filter
def isinst(value, class_str):
    classe = value.__class__.__name__
    return classe == class_str


@register.filter
def age(data):
    today = date.today()
    idade = relativedelta(today, data)
    years = '%s %s%s' % (
        idade.years if idade.years else '',
        _('ano') if idade.years else '',
        's' if idade.years > 1 else '')

    months = '%s%s %s%s' % (
        ', ' if idade.years and idade.months else '',
        idade.months if idade.months else '',
        _('mes') if idade.months else '',
        'es' if idade.months > 1 else '')
    days = '%s%s %s%s' % (
        ', ' if idade.days and (idade.months or idade.years) else '',
        idade.days if idade.days else '',
        _('dia') if idade.days else '',
        's' if idade.days > 1 else '')
    return '%s%s%s' % (years.strip(), months.strip(), days.strip())


@register.filter
def get_add_perm(value, arg):
    perm = value
    view = arg

    try:
        nome_app = view.__class__.model._meta.app_label
    except AttributeError:
        return None
    nome_model = view.__class__.model.__name__.lower()
    can_add = '.add_' + nome_model

    return perm.__contains__(nome_app + can_add)


@register.filter
def get_change_perm(value, arg):
    perm = value
    view = arg

    try:
        nome_app = view.__class__.model._meta.app_label
    except AttributeError:
        return None
    nome_model = view.__class__.model.__name__.lower()
    can_change = '.change_' + nome_model

    return perm.__contains__(nome_app + can_change)


@register.filter
def get_delete_perm(value, arg):
    perm = value
    view = arg

    try:
        nome_app = view.__class__.model._meta.app_label
    except AttributeError:
        return None
    nome_model = view.__class__.model.__name__.lower()
    can_delete = '.delete_' + nome_model

    return perm.__contains__(nome_app + can_delete)


@register.filter
def ultima_filiacao(value):
    parlamentar = value

    ultima_filiacao = Filiacao.objects.filter(
        parlamentar=parlamentar).order_by('-data').first()

    if ultima_filiacao:
        return ultima_filiacao.partido
    else:
        return None


@register.filter
def get_config_attr(attribute):
    return AppConfig.attr(attribute)


@register.filter
def str2intabs(value):
    if not isinstance(value, str):
        return ''
    try:
        v = int(value)
        v = abs(v)
        return v
    except:
        return ''


@register.filter
def url(value):
    if value.startswith('http://') or value.startswith('https://'):
        return True
    return False


@register.inclusion_tag('core/notificacoes_unread.html', takes_context=True)
def notificacoes_unread(context):

    try:
        request = context['request']

        if request.user.is_anonymous:
            return {'notificacoes_anonimas': [],
                    'notificacoes_usuarios': [],
                    'notificacoes': 0, }

        result = {'notificacoes_anonimas':
                  request.user.notificacao_set.unread().filter(
                      user_origin__isnull=True).order_by('-created'),
                  'notificacoes_usuarios':
                  request.user.notificacao_set.unread().filter(
                      user_origin__isnull=False).order_by('-created')
                  }

        result.update(
            {
                'notificacoes': (
                    result['notificacoes_anonimas'].count() +
                    result['notificacoes_usuarios'].count()),
            }
        )
        return result
    except:
        return None


@register.filter
def notificacoes_unread_count(user):
    if not user or user and user.is_anonymous:
        return 0

    return user.notificacao_set.unread().count()


@register.filter
def objeto_lido(obj, user):
    return not obj.notificacoes.unread().filter(user=user).exists()


@register.filter
def data_de_leitura(obj, user):
    qs = obj.notificacoes.read().filter(user=user)
    if not qs.exists():
        return None

    return qs.first().modified


@register.inclusion_tag('core/user/avatar.html')
def avatar_user(user_render=None):
    return {
        'user_render': user_render
    }


def get_as_tags(bundle_name, extension=None, config='DEFAULT', attrs=''):
    '''
    Get a list of formatted <script> & <link> tags for the assets in the
    named bundle.

    :param bundle_name: The name of the bundle
    :param extension: (optional) filter by extension, eg. 'js' or 'css'
    :param config: (optional) the name of the configuration
    :return: a list of formatted tags as strings
    '''

    bundle = _get_bundle(bundle_name, extension, config)
    tags = []
    for chunk in bundle:
        if chunk['name'].endswith(('.js', '.js.gz')):
            tags.append((
                '<script src="{0}" {1}></script>'
            ).format(chunk['url'], attrs))
        elif chunk['name'].endswith(('.css', '.css.gz')):
            tags.append((
                '<link type="text/css" href="{0}" rel="stylesheet" {1}/>'
            ).format(chunk['url'], attrs))
    return tags


@register.simple_tag
def render_bundle(bundle_name, extension=None, config='DEFAULT', attrs=''):
    tags = get_as_tags(bundle_name, extension=extension,
                       config=config, attrs=attrs)
    return mark_safe('\n'.join(tags))


@register.simple_tag
def settings_key_tag(var_name):
    return getattr(settings, var_name)


@register.filter
def settings_key_filter(var_name):
    return getattr(settings, var_name)


@register.simple_tag
def render_chunk_vendors(extension=None):
    try:
        tags = utils.get_as_tags(
            'chunk-vendors', extension=extension, config='DEFAULT', attrs='')
        return mark_safe('\n'.join(tags))
    except:
        return ''


@register.simple_tag(takes_context=True)
def yaml_render(context, template_name, increment_space=0):
    t = template.loader.get_template(template_name)
    r = t.template.render(context)
    if not increment_space:
        return r

    r = r.split('\n')
    r = ['%s%s' % (' ' * increment_space, line) for line in r]
    return mark_safe('\n'.join(r))


@register.filter(is_safe=True)
@stringfilter
def dont_break_out(value):
    _safe = '<div class="dont-break-out">{}</div>'.format(value)
    _safe = mark_safe(_safe)
    return _safe


@register.filter
def sidebar_tipos_de_normas(obj):
    return TipoNormaJuridica.objects.all()


@register.filter
def sidebar_tipos_de_materias(obj):
    return TipoMateriaLegislativa.objects.all().order_by('sequencia_regimental')


@register.filter
def normas_de_destaque(obj):
    return NormaJuridica.objects.filter(norma_de_destaque=True).order_by('id')


@register.filter
def timedelta_filter(data, td):
    if not data:
        data = timezone.now()
    data += timedelta(days=int(td))
    return data


@register.filter
def now_year(obj):
    return timezone.now().year


@register.filter(expects_localtime=True)
def parse_datetime(value):
    return django_parse_datetime(value)


@register.filter
def conteudo_protocolado_homologado(protocolo):
    cp = protocolo.conteudo_protocolado

    if not cp:
        return False

    if not hasattr(cp, 'FIELDFILE_NAME'):
        return False

    fieldfile_name = cp.FIELDFILE_NAME

    homologado = True
    for fn in fieldfile_name:

        try:
            homologado = not not cp.metadata['signs'][fn]['hom']
        except:
            return False

        if not homologado:
            return False
    return True
