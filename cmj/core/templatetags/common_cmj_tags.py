from datetime import date

from compressor.utils import get_class
from dateutil.relativedelta import relativedelta
from django import template
from django.contrib.auth.tokens import default_token_generator
from django.db.models.query import QuerySet
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from sapl.base.models import AppConfig
from sapl.parlamentares.models import Filiacao


register = template.Library()


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
    return model._meta.verbose_name_plural


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
    request = context['request']

    if request.user.is_anonymous():
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


@register.filter
def notificacoes_unread_count(user):
    if user and user.is_anonymous():
        return 0
    return user.notificacao_set.unread().count()

@register.filter
def objeto_lido(obj, user):
    return not obj.notificacoes.unread().filter(user=user).exists()
