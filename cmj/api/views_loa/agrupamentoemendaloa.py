from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from cmj.api.views_loa.emendaloa import EmendaLoaViewSet
from cmj.loa.models import AgrupamentoEmendaLoa, EmendaLoa


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

        AgrupamentoEmendaLoa.objects.filter(
            agrupamento=int(request.data["agrupamento"]),
            emendaloa=int(request.data["emendaloa"]),
        ).delete()

        return Response({"detail": "Registro removido com Sucesso."})

    def create(self, request, *args, **kwargs):
        try:
            r = super().create(request, *args, **kwargs)

            emendaloa__fase = request.data.get("emendaloa__fase", None)
            if emendaloa__fase:
                el = EmendaLoa.objects.get(pk=r.data["emendaloa"])
                el.fase = emendaloa__fase
                el.save()

            return r
        except Exception as e:
            if "code='unique'" in str(e):
                raise DRFValidationError(
                    "Esta Emenda impositiva já está adicionada em outro Agrupamento."
                )
            raise DRFValidationError(e)
