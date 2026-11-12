import pymupdf
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework.decorators import action

from cmj.api.loa.views.emendaloa import EmendaLoaSearchSerializer, EmendaLoaViewSet
from cmj.loa.models import EmendaLoa
from cmj.utils.utils_report import make_pdf
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

    @action(
        methods=[
            "get",
        ],
        detail=True,
    )
    def view(self, request, *args, **kwargs):
        base_url = request.build_absolute_uri()

        context = self.get_context_preview({})

        template = render_to_string("loa/pdf/agrupamento_preview.html", context)
        pdf_file = make_pdf(base_url=base_url, main_template=template)
        ext = "pdf"

        doc = pymupdf.Document(stream=pdf_file)

        p = int(request.GET.get("p", "0"))
        if p:
            d2b = doc
            ext = "png"
            page = doc[(p - 1) % len(doc)]
            d2b = page.get_pixmap(dpi=200)

            bresponse = d2b.tobytes()
            doc.close()
        else:
            bresponse = doc.tobytes()

        tipo = "emenda-impositiva-coletiva"

        arcname = "{}-{:04d}-{}{}.{}".format(
            context["agrupamento"]["object"].loa.ano,
            context["agrupamento"]["object"].id,
            tipo,
            f"-p{p}" if p else "",
            ext,
        )

        response = HttpResponse(
            bresponse, content_type="image/png" if p else "application/pdf"
        )
        response["Content-Disposition"] = f'inline; filename="{arcname}"'
        response["Cache-Control"] = "no-cache"
        response["Pragma"] = "no-cache"
        response["Expires"] = 0
        return response

    def get_context_preview(self, context):
        agrupamento = self.get_object()
        context["agrupamento"] = agrupamento.preparar_dados_para_coletiva()
        context["lineHeight"] = 1.2
        context["view"] = self

        return context

    @property
    def art(self):
        if not hasattr(self, "_art"):
            self._art = 0

        self._art += 1
        return self._art
