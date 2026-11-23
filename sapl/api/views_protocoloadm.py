from django.apps.registry import apps
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from cmj.core.models import AreaTrabalho
from drfautoapi.drfautoapi import (
    ApiViewSetConstrutor,
    BusinessRulesNotImplementedMixin,
    customize,
    wrapper_queryset_response_for_drf_action,
)
from sapl.api.mixins import (
    ControlAccessFileForContainerMixin,
    RegistrosDaAreaDoOperadorMixin,
)
from sapl.api.permissions import ContainerPermission, SaplModelPermissions
from sapl.base.models import AppConfig
from sapl.protocoloadm.models import (
    Anexado,
    DocumentoAcessorioAdministrativo,
    DocumentoAdministrativo,
    StatusTramitacaoAdministrativo,
    TipoDocumentoAdministrativo,
    TramitacaoAdministrativo,
)

ApiViewSetConstrutor.build_class([apps.get_app_config("protocoloadm")])


@customize(TipoDocumentoAdministrativo)
class _TipoDocumentoAdministrativoViewSet(
    BusinessRulesNotImplementedMixin, ControlAccessFileForContainerMixin
):
    container_field = "workspace__operadores"
    permission_classes = (ContainerPermission,)


@customize(DocumentoAdministrativo)
class _DocumentoAdministrativoViewSet(
    BusinessRulesNotImplementedMixin, ControlAccessFileForContainerMixin
):
    container_field = "workspace__operadores"
    permission_classes = (ContainerPermission,)

    def get_queryset(self):
        qs = ControlAccessFileForContainerMixin.get_queryset(self)
        if self.action == "texto_integral":

            pk = self.kwargs["pk"]
            if not self.link_share:
                d = qs.filter(pk=pk).first()
            else:

                qs = DocumentoAdministrativo.objects.filter(pk=pk)

                item = qs.first()

                if item and item.visibilidade != item.STATUS_DOC_ADM_PUBLICO:
                    raise PermissionDenied("Arquivo de Acesso restrito!")

                def check_hash_parent(d, hash):
                    if d.link_share == hash:
                        return True
                    while d.documento_anexado_set.exists():
                        parents = d.documento_anexado_set.all()
                        for p in parents:
                            return check_hash_parent(p.documento_principal, hash)
                    return False

                if check_hash_parent(item, self.link_share):
                    return qs
                else:
                    raise PermissionDenied("HashCode de compartilhamento não confere!")

            if not d:
                qs_new = DocumentoAdministrativo.objects.filter(pk=pk)
                d = qs_new.first()

                if d and (d.materia or d.vinculodocadminmateria_set.exists()):
                    if d.workspace.tipo == AreaTrabalho.TIPO_PUBLICO:
                        return qs_new
                    elif d.workspace.tipo == AreaTrabalho.TIPO_PROCURADORIA:
                        # API-ARQ-024: o parecer da Procuradoria vinculado a
                        # matéria é público, como na página da matéria
                        # (docs/specs/api/arquivos.md)
                        return qs_new
        return qs

    @action(detail=True)
    def texto_integral(self, request, *args, **kwargs):
        self.link_share = request.GET.get("hash", "")
        return self.response_file(request, *args, **kwargs)


@customize(DocumentoAcessorioAdministrativo)
class _DocumentoAcessorioAdministrativoViewSet(
    BusinessRulesNotImplementedMixin, ControlAccessFileForContainerMixin
):
    container_field = "documento__workspace__operadores"
    permission_classes = (ContainerPermission,)

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)


@customize(TramitacaoAdministrativo)
class _TramitacaoAdministrativoViewSet(
    BusinessRulesNotImplementedMixin, ControlAccessFileForContainerMixin
):
    container_field = "documento__workspace__operadores"
    permission_classes = (ContainerPermission,)


@customize(Anexado)
class _AnexadoViewSet(
    BusinessRulesNotImplementedMixin, ControlAccessFileForContainerMixin
):
    container_field = "documento_principal__workspace__operadores"
    permission_classes = (ContainerPermission,)


@customize(StatusTramitacaoAdministrativo)
class _StatusTramitacaoAdministrativoViewSet(RegistrosDaAreaDoOperadorMixin):
    pass
