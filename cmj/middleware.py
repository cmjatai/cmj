import logging
import re

from django.db.models import Q
from django.http.response import HttpResponse, Http404, HttpResponseForbidden,\
    HttpResponseRedirect
from django.urls.base import resolve
from django.utils import timezone
import yaml

from cmj.utils import get_breadcrumb_classes
from sapl.base.models import AppConfig


logger = logging.getLogger(__name__)


class DisabledMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Código de inicialização do Middleware

    def __call__(self, request):
        # Aqui vai o código a ser executado antes
        # da View e de outros middlewares
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv

        response = self.get_response(request)

        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # Aqui vai o código a ser executado
        # para cada resposta após a View

        return response

    def process_view(self, request, func, args, kwargs):
        # Esse método é chamado logo antes do Django executar a View que vai
        # processar a requisição e possui os seguintes parâmetros:
        # None - continua as midd
        # httpreponse responde

        now = timezone.localtime()
        path = request.path
        try:

            if path == '/login' or path.startswith('/sistema/app'):
                return

            self.periodos = yaml.full_load(AppConfig.attr('disabled'))

            for pdict in self.periodos:

                start = pdict.get('start', None)
                end = pdict.get('end', None)

                if start and end and (now < start or now > end):
                    continue

                if start and now < start:
                    continue

                if end and now > end:
                    continue

                urls = pdict.get('urls', [])
                for udict in urls:
                    if not udict:
                        continue

                    url = udict.get('url', '/') or '/'
                    url = url.split(',')

                    r = re.compile(url[0].strip(), re.I)
                    m = r.findall(path)

                    if m:
                        # print(path, 'BLOCK')
                        if len(url) == 2:
                            return HttpResponseRedirect(url[1].strip())
                        else:
                            return HttpResponseForbidden()

        except:
            self.periodos = []
            logger.error(
                'Erro na carga e avaliação dos períodos e suas urls desativadas')

        # print(timezone.localtime() - now, path)

    def process_exception(self, request, exception):
        pass

    def process_template_response(self, request, response):
        return response


class BreadCrumbMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, func, args, kwargs):
        pass

    def process_exception(self, request, exception):
        pass

    def process_template_response(self, request, response):
        try:
            context = response.context_data

            if request.path.startswith('/api/') or not context:
                return response

            return get_breadcrumb_classes(context, request, response)
        except:
            return response
