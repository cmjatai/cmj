from django.apps.registry import apps

from drfautoapi.drfautoapi import (
    ApiViewSetConstrutor,
    customize,
    wrapper_queryset_response_for_drf_action,
)
from sapl.compilacao.models import (
    Dispositivo,
    Nota,
    Publicacao,
    TextoArticulado,
    Vide,
)
from sapl.compilacao.services.s_visibilidade import VisibilidadeCompilacaoService

ApiViewSetConstrutor.build_class([apps.get_app_config("compilacao")])

visibilidade = VisibilidadeCompilacaoService()


@customize(TextoArticulado)
class _TextoArticuladoViewSet:

    def get_queryset(self):
        return visibilidade.textos_visiveis(self.request.user, super().get_queryset())


@customize(Dispositivo)
class _DispositivoViewSet:

    def get_queryset(self):
        return visibilidade.dispositivos_visiveis(
            self.request.user, super().get_queryset()
        )


@customize(Publicacao)
class _PublicacaoViewSet:

    def get_queryset(self):
        return visibilidade.publicacoes_visiveis(
            self.request.user, super().get_queryset()
        )


@customize(Vide)
class _VideViewSet:

    def get_queryset(self):
        return visibilidade.vides_visiveis(self.request.user, super().get_queryset())


@customize(Nota)
class _NotaViewSet:

    def get_queryset(self):
        return visibilidade.notas_visiveis(self.request.user, super().get_queryset())
