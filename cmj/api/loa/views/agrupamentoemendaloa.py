import logging

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from cmj.api.loa.views.emendaloa import EmendaLoaViewSet
from cmj.loa.models import AgrupamentoEmendaLoa, EmendaLoa
from cmj.loa.models.m_agrupamento import Agrupamento
from cmj.utils.genia.loa_agrupamento import IAEmentaEmendaColetivaError

logger = logging.getLogger(__name__)


class AgrupamentoEmendaLoaViewSet:

    class AgrupamentoEmendaLoaPermission(EmendaLoaViewSet.EmendaLoaPermission):
        def has_permission_post(self, request, view):
            return request.user.has_perm("loa.emendaloa_full_editor")

        has_permission_delete = has_permission_post
        has_permission_patch = has_permission_post

    permission_classes = (AgrupamentoEmendaLoaPermission,)

    @action(
        methods=[
            "post",
        ],
        detail=False,
    )
    def delete(self, request, *args, **kwargs):

        agrupamento_emenda = AgrupamentoEmendaLoa.objects.filter(
            agrupamento=int(request.data["agrupamento"]),
            emendaloa=int(request.data["emendaloa"]),
        ).first()

        if not agrupamento_emenda:
            raise DRFValidationError("Registro não encontrado.")

        if agrupamento_emenda.emendaloa.fase == EmendaLoa.TRANSFORMADA_EM_COLETIVA:
            raise DRFValidationError(
                "Não é possível remover Emenda de um agrupamento transformado em coletiva."
            )

        agrupamento = agrupamento_emenda.agrupamento
        try:
            # sync agrupamento
            agrupamento.sync()

            # sync emenda
            emendaloa_id = int(request.data["emendaloa"])
            emendaloa = EmendaLoa.objects.get(pk=emendaloa_id)
            emendaloa.sync()
        except Exception as e:
            logger.error("Erro ao sincronizar agrupamento e emenda: %s", e)

        agrupamento_emenda.delete()

        # a finalidade é gerada depois da remoção, já sem a emenda removida
        aviso_finalidade = self.atualizar_finalidade(agrupamento)

        return Response(
            {
                "detail": "Registro removido com Sucesso.",
                "agrupamento_finalidade": agrupamento.finalidade,
                "aviso_finalidade": aviso_finalidade,
            }
        )

    @staticmethod
    def atualizar_finalidade(agrupamento):
        """Gera a finalidade com I.A. e devolve o aviso de falha da I.A., ou ""."""
        try:
            agrupamento.update_finalidade_com_ia()
        except IAEmentaEmendaColetivaError as e:
            return str(e)
        except Exception as e:
            # sem emendas ou com unidades e entidades diferentes não há aviso
            logger.error("Erro ao atualizar finalidade com IA: %s", e)
        return ""

    FASES_PERMITIDAS_NA_INCLUSAO = (
        EmendaLoa.PROPOSTA_LIBERADA,
        EmendaLoa.EDICAO_CONTABIL,
    )

    def validar_inclusao(self, request):
        try:
            agrupamento = Agrupamento.objects.get(pk=int(request.data["agrupamento"]))
            el = EmendaLoa.objects.get(pk=int(request.data["emendaloa"]))
        except (KeyError, TypeError, ValueError, Agrupamento.DoesNotExist):
            raise DRFValidationError("Agrupamento ou Emenda inválidos.")
        except EmendaLoa.DoesNotExist:
            raise DRFValidationError("Emenda Impositiva não encontrada.")

        if el.fase not in self.FASES_PERMITIDAS_NA_INCLUSAO:
            raise DRFValidationError(
                "Só é possível adicionar ao agrupamento Emendas nas fases "
                f'"{dict(EmendaLoa.FASE_CHOICE)[EmendaLoa.PROPOSTA_LIBERADA]}" ou '
                f'"{dict(EmendaLoa.FASE_CHOICE)[EmendaLoa.EDICAO_CONTABIL]}".'
            )

        if el.loa.ano != agrupamento.loa.ano:
            raise DRFValidationError(
                "A Emenda Impositiva deve ser do mesmo ano da LOA do agrupamento."
            )

        return el

    def create(self, request, *args, **kwargs):
        # a fase resultante é definida aqui; emendaloa__fase enviado pelo cliente é ignorado
        el = self.validar_inclusao(request)
        try:
            r = super().create(request, *args, **kwargs)

            el.refresh_from_db()
            if el.fase != EmendaLoa.EDICAO_CONTABIL:
                el.fase = EmendaLoa.EDICAO_CONTABIL
                el._usuario_fase = request.user  # LOA-FASE-067
                el.save()

            agrupamento = Agrupamento.objects.get(pk=int(request.data["agrupamento"]))
            r.data["aviso_finalidade"] = self.atualizar_finalidade(agrupamento)
            r.data["agrupamento_finalidade"] = agrupamento.finalidade

            return r
        except Exception as e:
            if "code='unique'" in str(e):
                raise DRFValidationError(
                    "Esta Emenda impositiva já está adicionada em outro Agrupamento."
                )
            raise DRFValidationError(e)
