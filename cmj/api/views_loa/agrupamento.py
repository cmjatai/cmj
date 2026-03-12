from rest_framework.decorators import action

from cmj.api.views_loa.emendaloa import EmendaLoaSearchSerializer, EmendaLoaViewSet
from cmj.loa.models import EmendaLoa
from drfautoapi.drfautoapi import wrapper_queryset_response_for_drf_action


class AgrupamentoViewSet:

    class AgrupamentoPermission(EmendaLoaViewSet.EmendaLoaPermission):
        def has_permission_post(self, request, view):
            return request.user.has_perm("loa.emendaloa_full_editor")

        has_permission_delete = has_permission_post
        has_permission_patch = has_permission_post

    permission_classes = (AgrupamentoPermission,)

    @action(
        methods=[
            "get",
        ],
        detail=True,
    )
    def emendas(self, request, *args, **kwargs):
        return self.get_emendas(**kwargs)

    @wrapper_queryset_response_for_drf_action(model=EmendaLoa)
    def get_emendas(self, **kwargs):
        self.serializer_class = EmendaLoaSearchSerializer
        qs = self.get_queryset()
        return qs.filter(agrupamentoemendaloa__agrupamento_id=kwargs["pk"])
