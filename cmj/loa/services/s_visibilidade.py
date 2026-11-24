from django.db.models import Q

from cmj.loa.services.s_emendaloa import EmendaLoaService


class VisibilidadeLoaService:
    """Quem consulta os registros que pertencem a uma LOA
    (docs/specs/api/acesso.md).

    Todo registro que pertence a uma LOA segue a visibilidade dela, a mesma da
    lista de LOAs e das emendas (``EmendaLoaService.loas_visiveis``): anônimo e
    conta comum só veem LOA publicada; operador de autor vê também a não
    publicada cuja matéria ainda não virou norma; quem tem
    ``loa.emendaloa_full_editor`` vê todas.
    """

    # caminho de cada model até a LOA; mais de um caminho quando o registro
    # pertence à LOA por um vínculo ou por outro
    CAMINHOS = {
        "loa": ("pk",),
        "loaparlamentar": ("loa",),
        "emendaloa": ("loa",),
        "emendaloaparlamentar": ("emendaloa__loa",),
        "emendaloahistoricofase": ("emendaloa__loa",),
        "emendaloaregistrocontabil": ("emendaloa__loa",),
        "oficioajusteloa": ("loa",),
        "registroajusteloa": ("oficio_ajuste_loa__loa",),
        "registroajusteloaparlamentar": ("registro__oficio_ajuste_loa__loa",),
        "agrupamento": ("loa",),
        "agrupamentoemendaloa": ("agrupamento__loa",),
        "agrupamentoregistrocontabil": ("agrupamento__loa",),
        "orgao": ("loa",),
        "unidadeorcamentaria": ("loa",),
        "funcao": ("loa",),
        "subfuncao": ("loa",),
        "programa": ("loa",),
        "acao": ("loa",),
        "fonte": ("loa",),
        "natureza": ("loa",),
        "despesa": ("loa",),
        "despesaconsulta": ("loa",),
        "receitaorcamentaria": ("orgao__loa",),
        "receitaarrecadada": ("receita__orgao__loa",),
        "despesapaga": ("orgao__loa",),
        "empenho": ("orgao__loa",),
        "empenhoemendaajuste": (
            "emendaloa__loa",
            "ajuste__oficio_ajuste_loa__loa",
        ),
        "prestacaocontaloa": ("loa",),
        "arquivoprestacaocontaloa": ("prestacao_conta__loa",),
        "prestacaocontaregistro": ("prestacao_conta__loa",),
        "arquivoprestacaocontaregistro": ("registro__prestacao_conta__loa",),
    }

    @staticmethod
    def ve_todas(user):
        return bool(
            user
            and not user.is_anonymous
            and user.has_perm("loa.emendaloa_full_editor")
        )

    def loa_visivel(self, user, loa):
        if self.ve_todas(user):
            return True
        return EmendaLoaService.loas_visiveis(user).filter(pk=loa.pk).exists()

    def visiveis(self, user, queryset):
        """Os registros de ``queryset`` que ``user`` consulta. O caminho até a
        LOA vem do model do queryset; model sem LOA não é filtrado."""
        caminhos = self.CAMINHOS.get(queryset.model._meta.model_name)
        if not caminhos or self.ve_todas(user):
            return queryset

        loas = EmendaLoaService.loas_visiveis(user).values("pk")
        filtro = Q()
        for caminho in caminhos:
            filtro |= Q(**{f"{caminho}__in": loas})
        return queryset.filter(filtro)
