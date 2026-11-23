class ChatHistoricoService:
    """Quem consulta as sessões e as mensagens do chat (docs/specs/api/acesso.md).

    Cada usuário consulta só as próprias sessões e as mensagens delas, qualquer
    que seja a permissão que tenha. Sem usuário autenticado, nada é consultado.
    """

    @staticmethod
    def sessoes_do_usuario(user, queryset):
        if not user or user.is_anonymous:
            return queryset.none()
        return queryset.filter(user=user)

    @staticmethod
    def mensagens_do_usuario(user, queryset):
        if not user or user.is_anonymous:
            return queryset.none()
        return queryset.filter(chat__user=user)

    @staticmethod
    def e_dono_da_sessao(user, sessao):
        """Só o dono grava mensagem na sessão."""
        return bool(user and not user.is_anonymous and sessao.user_id == user.id)
