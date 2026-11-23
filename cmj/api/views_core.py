import logging

from django.apps.registry import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http.response import Http404
from django.utils.text import slugify
from rest_framework.decorators import action
from rest_framework.response import Response

from cmj.api.serializers import BiSerializer
from cmj.core.models import AuditLog, Bi, CertidaoPublicacao
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.mixins import ResponseFileMixin

logger = logging.getLogger(__name__)

# Sem rota na API: o model de usuário (senha, grupos e permissões são
# administrados só pelas telas de usuário) e o registro de auditoria
# (consultado só pela tela de pesquisa).
MODELS_SEM_ROTA = (get_user_model(), AuditLog)

ApiViewSetConstrutor.build_class(
    [
        model
        for model in apps.get_app_config("core").get_models()
        if model not in MODELS_SEM_ROTA
    ]
)


@customize(Bi)
class _BiViewSet:
    serializer_class = BiSerializer


@customize(CertidaoPublicacao)
class _CertidaoPublicacaoViewSet(ResponseFileMixin):

    def custom_filename__(self, item):
        arcname = "{}-{}.{}".format(
            item.loa.ano, slugify(item.epigrafe), item.arquivo.path.split(".")[-1]
        )
        return arcname

    @action(detail=True)
    def certificado(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
