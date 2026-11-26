import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

logger = logging.getLogger(__name__)


class AgrupamentoService:
    """Regras da tela de edição do agrupamento (docs/specs/loa/edicao-agrupamento.md)."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AgrupamentoService, cls).__new__(cls)
        return cls._instance

    # ------------------------------------------------- devolução para correção

    @staticmethod
    def fases_devolviveis():
        """Fases em que a emenda é devolvida pela tela do agrupamento (LOA-AGR-091, D8)."""
        from cmj.loa.models import EmendaLoa

        return (
            EmendaLoa.PROPOSTA_LIBERADA,
            EmendaLoa.EDICAO_CONTABIL,
            EmendaLoa.LIBERACAO_CONTABIL,
        )

    def validar_devolucao(self, user, agrupamento, emenda):
        """Confere se ``user`` pode devolver ``emenda`` pela tela de ``agrupamento``.

        Devolve o vínculo da emenda com ``agrupamento``, ou None quando ela não está
        em agrupamento. Levanta ``PermissionDenied`` ou ``ValidationError``
        (LOA-AGR-091, 092 e 095).
        """
        from cmj.loa.models import AgrupamentoEmendaLoa, EmendaLoa

        if (
            not user
            or user.is_anonymous
            or not user.has_perm("loa.emendaloa_full_editor")
        ):
            raise PermissionDenied(
                "Você não tem permissão para devolver Emendas para correção."
            )

        if emenda.loa_id != agrupamento.loa_id:
            raise ValidationError("A Emenda não é da LOA deste agrupamento.")

        # LOA-FASE-072: a coletiva não volta para a fase 10
        EmendaLoa.service.validar_fase_da_coletiva(emenda, EmendaLoa.PROPOSTA)

        if emenda.fase not in self.fases_devolviveis():
            fases = dict(EmendaLoa.FASE_CHOICE)
            nomes = ", ".join(f'"{fases[f]}"' for f in self.fases_devolviveis())
            raise ValidationError(
                f"Só é possível devolver para correção Emendas nas fases {nomes}."
            )

        vinculo = (
            AgrupamentoEmendaLoa.objects.filter(emendaloa=emenda)
            .select_related("agrupamento")
            .first()
        )
        if vinculo and vinculo.agrupamento_id != agrupamento.pk:
            raise ValidationError(
                f'A Emenda está no agrupamento "{vinculo.agrupamento.nome}". '
                "Devolva-a por lá."
            )
        return vinculo

    def devolver_emenda(self, user, agrupamento, emenda):
        """Devolve ``emenda`` para a fase 10 pela tela de ``agrupamento`` (LOA-AGR-091).

        Se a emenda está neste agrupamento, sai dele como na lixeira (LOA-AGR-043 e
        092), com os registros contábeis sincronizados. Devolve True quando ela saiu
        do agrupamento: quem chama gera de novo a finalidade dele.
        """
        from cmj.loa.models import EmendaLoa

        vinculo = self.validar_devolucao(user, agrupamento, emenda)

        with transaction.atomic():
            if vinculo:
                # mesmos passos da lixeira: os registros ficam com a emenda (LOA-AGR-046)
                try:
                    agrupamento.sync()
                    emenda.sync()
                except Exception as e:
                    logger.error("Erro ao sincronizar agrupamento e emenda: %s", e)
                vinculo.delete()

            emenda.refresh_from_db()
            emenda.fase = EmendaLoa.PROPOSTA
            emenda._usuario_fase = user  # LOA-FASE-067
            emenda.save()

        return vinculo is not None
