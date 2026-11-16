import logging

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from cmj.api.loa.views.emendaloa import EmendaLoaViewSet
from cmj.loa.models import AgrupamentoEmendaLoa, EmendaLoa
from cmj.loa.models.m_agrupamento import Agrupamento

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

        try:
            # sync agrupamento
            agrupamento_id = int(request.data["agrupamento"])
            agrupamento = Agrupamento.objects.get(pk=agrupamento_id)
            agrupamento.sync()
            agrupamento.update_finalidade_com_ia()

            # sync emenda
            emendaloa_id = int(request.data["emendaloa"])
            emendaloa = EmendaLoa.objects.get(pk=emendaloa_id)
            emendaloa.sync()
        except Exception as e:
            logger.error("Erro ao atualizar finalidade com IA: %s", e)

        agrupamento_emenda.delete()

        return Response({"detail": "Registro removido com Sucesso."})

    def create(self, request, *args, **kwargs):
        try:
            r = super().create(request, *args, **kwargs)

            emendaloa__fase = request.data.get("emendaloa__fase", None)
            if emendaloa__fase:
                el = EmendaLoa.objects.get(pk=r.data["emendaloa"])
                el.fase = emendaloa__fase
                el.save()

            r.data["agrupamento_finalidade"] = AgrupamentoEmendaLoa.objects.get(
                agrupamento=int(request.data["agrupamento"]),
                emendaloa=int(request.data["emendaloa"]),
            ).agrupamento.finalidade

            try:
                agrupamento = Agrupamento.objects.get(
                    pk=int(request.data["agrupamento"])
                )
                agrupamento.update_finalidade_com_ia()
            except Exception as e:
                logger.error("Erro ao atualizar finalidade com IA: %s", e)

            return r
        except Exception as e:
            if "code='unique'" in str(e):
                raise DRFValidationError(
                    "Esta Emenda impositiva já está adicionada em outro Agrupamento."
                )
            raise DRFValidationError(e)
