import logging

from django.http.response import Http404
from django.shortcuts import redirect
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
            sr.metadata = request.META
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


class ShortAdminView(Crud):
    model = UrlShortener
    model_set = 'short_set'

    class ListView(Crud.ListView):
        paginate_by = 100
        ordering = '-id'
