class DraftService:
    """Quem consulta os drafts e as mídias deles (docs/specs/api/acesso.md).

    Cada usuário consulta só os próprios drafts e as mídias deles, qualquer que
    seja a permissão que tenha. Sem usuário autenticado, nada é consultado.
    """

    @staticmethod
    def drafts_do_usuario(user, queryset):
        if not user or user.is_anonymous:
            return queryset.none()
        return queryset.filter(owner=user)

    @staticmethod
    def midias_do_usuario(user, queryset):
        if not user or user.is_anonymous:
            return queryset.none()
        return queryset.filter(draft__owner=user)

    @staticmethod
    def e_dono_do_draft(user, draft):
        """Só o dono grava mídia no draft."""
        return bool(user and not user.is_anonymous and draft.owner_id == user.id)
