
from django.apps.registry import apps
from django.utils.text import slugify
from rest_framework.decorators import action

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl.api.mixins import ResponseFileMixin
from sapl.norma.models import NormaJuridica, AnexoNormaJuridica


ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('norma')
    ]
)


@customize(NormaJuridica)
class _NormaJuridicaViewset(ResponseFileMixin):

    def custom_filename(self, item):
        arcname = '{}-{}-{}-{}.{}'.format(
            item.ano,
            item.numero,
            slugify(item.tipo.sigla),
            slugify(item.tipo.descricao),
            item.texto_integral.path.split('.')[-1])
        return arcname

    @action(detail=False, methods=['GET'])
    def destaques(self, request, *args, **kwargs):
        self.queryset = self.get_queryset().filter(norma_de_destaque=True)
        return self.list(request, *args, **kwargs)

    @action(detail=True)
    def texto_integral(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)


@customize(AnexoNormaJuridica)
class _AnexoNormaJuridicaViewSet(ResponseFileMixin):

    @action(detail=True)
    def anexo_arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
