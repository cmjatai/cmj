from django import template


register = template.Library()


@register.simple_tag
def verbose_name(instance, field_name):
    return instance._meta.get_field(field_name).verbose_name.title()
