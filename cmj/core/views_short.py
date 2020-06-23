import logging

from django.http.response import Http404
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View

from cmj.sigad.models import UrlShortener, ShortRedirect
from sapl.crud.base import Crud


class ShortRedirectView(View):

    def get(self, request, *args, **kwargs):

        url = UrlShortener.objects.filter(url_short=kwargs['short']).first()
        if not url:
            raise Http404

        try:
            sr = ShortRedirect()
            sr.url = url
            sr.metadata = {
                'request': {
                    'meta': {
                        'HTTP_USER_AGENT': request.META.get('HTTP_USER_AGENT', ''),
                        'HTTP_X_FORWARDED_FOR': request.META.get('HTTP_X_FORWARDED_FOR', '')
                    }
                }
            }
            sr.save()
        except Exception as e:
            logger = logging.getLogger(__name__)
            self.logger.error('Erro: ' + str(e))

        return redirect(
            '{}{}'.format(
                '' if url.link_absoluto else '/',
                url.url_long
            )
        )


class ShortAdminCrud(Crud):
    model = UrlShortener

    class BaseMixin(Crud.BaseMixin):
        list_field_names = 'url_short', 'url_long', 'created', 'acessos_set'

    class ListView(Crud.ListView):
        paginate_by = 100
        ordering = '-id'

        def hook_header_acessos_set(self, *args, **kwargs):
            return _('Acessos')

        def hook_acessos_set(self, *args, **kwargs):
            return '', ''
