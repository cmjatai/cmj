from django import template
from django.conf import settings

register = template.Library()


def get_backend_info(backend):
    backend_info = getattr(settings, 'SOCIAL_BACKEND_INFO', dict())
    assert isinstance(backend_info, dict)
    return backend_info.get(backend)


@register.filter
def social_icon(backend):
    return get_backend_info(backend).get('icon')


@register.filter
def social_title(backend):
    return get_backend_info(backend).get('title')


@register.inclusion_tag('social_link_shares.html', takes_context=True)
def social_link_share(context, obj=None, css_class=''):

    url = obj.short_url()
    if not url:
        url = '%s://%s/%s' % (
            context['request'].scheme,
            context['request'].get_host(),
            obj.absolute_slug)

    return {'url': url,
        'text': obj.titulo,
        'css_class': css_class,}
