from django import template
from django.utils.safestring import mark_safe
from webpack_loader import utils


register = template.Library()


@register.simple_tag(takes_context=True)
def render_manifest(context, config='DEFAULT'):
    assets = utils.get_loader(config).get_assets()

    if assets.get('publicPath') == '/static/':
        return mark_safe(f'<link rel="manifest" href="{utils.get_static("manifest.json")}">')

    return ''
