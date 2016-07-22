from datetime import date

from compressor.utils import get_class
from dateutil.relativedelta import relativedelta
from django import template
from django.utils.translation import ugettext_lazy as _


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
def str2intabs(value):
    if not isinstance(value, str):
        return ''
    try:
        v = int(value)
        v = abs(v)
        return v
    except:
        return ''
