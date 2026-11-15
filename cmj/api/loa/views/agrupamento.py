import pymupdf
from django.http import HttpResponse, JsonResponse
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
            "post",
        ],
        detail=True,
    )
    def create_copia(self, request, *args, **kwargs):
        agrupamento = self.get_queryset().filter(id=kwargs["pk"]).first()
        if not agrupamento:
            return JsonResponse({"error": "Agrupamento not found"}, status=404)

        copia = agrupamento.create_copia()
        return JsonResponse({"pk": copia.id})

    @action(
        methods=[
            "patch",
        ],
        detail=True,
    )
    def generate_finalidade_global(self, request, *args, **kwargs):
        agrupamento = self.get_queryset().filter(id=kwargs["pk"]).first()
        finalidade_global = ""
        try:
            if agrupamento:
                agrupamento.update_finalidade_com_ia()
                finalidade_global = agrupamento.finalidade
            return JsonResponse({"finalidade_global": finalidade_global})
        except ValueError as e:
            # responder com erro para que o promise no frontend saiba que houve falha
            return JsonResponse({"error": str(e)}, status=400)

    @action(
        methods=[
            "get",
        ],
        detail=True,
    )
    def view(self, request, *args, **kwargs):
        base_url = request.build_absolute_uri()

        agrupamento = self.get_object()
        emendas_coletivas_structured = agrupamento.preparar_dados_para_coletiva()

        p = int(request.GET.get("p", "0"))
        doc = pymupdf.Document()
        for idx, emenda_coletiva in enumerate(emendas_coletivas_structured):
            self._art = 0
            context = {}
            context["lineHeight"] = 1.2
            context["view"] = self
            context["agrupamento"] = emenda_coletiva

            template = render_to_string("loa/pdf/agrupamento_preview.html", context)
            pdf_file = make_pdf(base_url=base_url, main_template=template)

            doc_individual = pymupdf.Document(stream=pdf_file)
            emenda_coletiva["doc"] = doc_individual
            doc.insert_pdf(doc_individual)

        # doc to byte
        bresponse = doc.write()

        for emenda_coletiva in emendas_coletivas_structured:
            emenda_coletiva["doc"].close()

        # reopen the merged document for reading
        doc = pymupdf.Document(stream=bresponse)
        ext = "pdf"

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

    @property
    def art(self):
        if not hasattr(self, "_art"):
            self._art = 0

        self._art += 1
        return self._art
