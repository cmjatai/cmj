import logging

from django.contrib import messages
from django.http.response import Http404
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View

from cmj.core.forms import UrlShortenerForm
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
    ordered_list = False

    class BaseMixin(Crud.BaseMixin):
        list_field_names = 'url_short', 'url_long', 'created', 'acessos_set'

        @property
        def update_url(self):
            if self.object.automatico:
                return None
            return super().update_url

        @property
        def delete_url(self):
            if self.object.automatico:
                return None
            return super().delete_url

    class ListView(Crud.ListView):
        paginate_by = 100
        ordering = '-id'

        def hook_header_acessos_set(self, *args, **kwargs):
            return 'Acessos'

        def hook_acessos_set(self, *args, **kwargs):
            return args[0].acessos_set.count(), ''

        def hook_url_short(self, *args, **kwargs):
            return """
                <div class="text-center">
                    <a class="d-inline-block" href="{}">{}</a>
                    <a class="copylink" title="Copiar Link" data_href="{}">
                      <span class="d-none">Copiar Link</span>
                    </a>
                </div>
            """.format(
                args[2],
                args[0].absolute_short,
                args[0].absolute_short
            ), ''

    class DetailView(Crud.DetailView):
        layout_key = 'UrlShortenerDetail'

        def get(self, request, *args, **kwargs):
            r = Crud.DetailView.get(self, request, *args, **kwargs)
            if self.object.automatico:
                messages.info(
                    self.request,
                    _(
                        'Link Automáticos não podem ser '
                        'editados e/ou excluídos.'
                    )
                )
            return r

    class CreateView(Crud.CreateView):
        form_class = UrlShortenerForm
