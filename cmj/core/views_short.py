from django.http.response import Http404
from django.shortcuts import redirect
from django.views.generic.base import View

from cmj.sigad.models import UrlShortener, ShortRedirect


class ShortRedirectView(View):

    def get(self, request, *args, **kwargs):

        try:
            url = UrlShortener.objects.get(url_short=kwargs['short'])
        except:
            raise Http404

        sr = ShortRedirect()
        sr.url = url
        sr.metadata = request.META
        sr.save()

        return redirect(
            '{}{}'.format(
                '' if url.link_absoluto else '/',
                url.url_long
            )
        )
