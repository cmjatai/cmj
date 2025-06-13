import logging

from django import template

logger = logging.getLogger(__name__)

register = template.Library()

@register.simple_tag(takes_context=True)
def container_css_class(context):
    css_class = context.get('container_css_class', None)
    if css_class:
        return css_class

    view = context.get('view', {})
    crud = getattr(view, 'crud', None)
    if crud:
        return crud.container_css_class

    if hasattr(view, 'container_css_class'):
        return view.container_css_class

    return 'container'

@register.filter
def to_dict(arg):
    return arg.__dict__

def to_dict(arg):
    return arg.__dict__
