from django.db.models import Q

from sapl.compilacao.models import (
    NINST,
    NPRIV,
    NPUBL,
    STATUS_TA_EDITION,
    STATUS_TA_IMMUTABLE_PUBLIC,
    STATUS_TA_IMMUTABLE_RESTRICT,
    STATUS_TA_PUBLIC,
    TextoArticulado,
)


class VisibilidadeCompilacaoService:
    """Quem consulta os textos articulados e o que pertence a eles
    (docs/specs/api/acesso.md).

    Segue ``TextoArticulado.has_view_permission`` e a exibição das notas nas
    telas: texto público sai para todos; os demais, para o dono ou para quem
    tem a permissão do estado. O texto privado só sai para o dono.
    """

    ESTADOS_PUBLICOS = (STATUS_TA_PUBLIC, STATUS_TA_IMMUTABLE_PUBLIC)
    PERMISSAO_DO_ESTADO = {
        STATUS_TA_IMMUTABLE_RESTRICT: "compilacao.view_restricted_textoarticulado",
        STATUS_TA_EDITION: "compilacao.change_dispositivo_edicao_dinamica",
    }

    def _filtro_do_texto(self, user, caminho=""):
        """``Q`` dos textos que ``user`` consulta. ``caminho`` leva do model
        filtrado até o texto articulado (``"ta__"``, por exemplo)."""
        filtro = Q(**{f"{caminho}privacidade__in": self.ESTADOS_PUBLICOS})
        if not user or user.is_anonymous:
            return filtro

        estados = [
            estado
            for estado, permissao in self.PERMISSAO_DO_ESTADO.items()
            if user.has_perm(permissao)
        ]
        if estados:
            filtro |= Q(**{f"{caminho}privacidade__in": estados})

        proprios = TextoArticulado.objects.filter(owners=user).values("pk")
        return filtro | Q(**{f"{caminho}pk__in": proprios})

    def textos_visiveis(self, user, queryset):
        return queryset.filter(self._filtro_do_texto(user))

    def dispositivos_visiveis(self, user, queryset):
        return queryset.filter(self._filtro_do_texto(user, "ta__"))

    def publicacoes_visiveis(self, user, queryset):
        return queryset.filter(self._filtro_do_texto(user, "ta__"))

    def vides_visiveis(self, user, queryset):
        return queryset.filter(self._filtro_do_texto(user, "dispositivo_base__ta__"))

    def notas_visiveis(self, user, queryset):
        """Notas de dispositivos de textos visíveis, conforme a publicidade:
        pública para todos, institucional para quem está autenticado e
        privada para o dono. Superusuário consulta todas."""
        queryset = queryset.filter(self._filtro_do_texto(user, "dispositivo__ta__"))
        if not user or user.is_anonymous:
            return queryset.filter(publicidade=NPUBL)
        if user.is_superuser:
            return queryset
        return queryset.filter(
            Q(publicidade__in=(NPUBL, NINST)) | Q(publicidade=NPRIV, owner=user)
        )
