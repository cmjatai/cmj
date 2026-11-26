import pymupdf
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from cmj.api.loa.views.emendaloa import EmendaLoaSearchSerializer, EmendaLoaViewSet
from cmj.loa.models import Agrupamento, EmendaLoa
from cmj.utils.genia.loa_agrupamento import IAEmentaEmendaColetivaError
from cmj.utils.utils_report import make_pdf, pdf_base_url
from drfautoapi.drfautoapi import wrapper_queryset_response_for_drf_action


class AgrupamentoViewSet:

    class AgrupamentoPermission(EmendaLoaViewSet.EmendaLoaPermission):
        def has_permission_post(self, request, view):
            return request.user.has_perm("loa.emendaloa_full_editor")

        has_permission_delete = has_permission_post
        has_permission_patch = has_permission_post

    permission_classes = (AgrupamentoPermission,)

    class AgrupamentoEditorPermission(AgrupamentoPermission):
        # LOA-AGR-003: a prévia também exige a permissão de edição no GET
        def has_permission_get(self, request, view):
            return self.has_permission_post(request, view)

    def perform_update(self, serializer):
        # LOA-AGR-053: finalidade enviada pelo autosave é digitada; vazia volta ao
        # modo automático
        if "finalidade" in serializer.validated_data:
            finalidade = serializer.validated_data["finalidade"] or ""
            serializer.save(finalidade_manual=bool(finalidade.strip()))
            return
        serializer.save()

    @action(
        methods=[
            "get",
        ],
        detail=True,
    )
    def emendas(self, request, *args, **kwargs):
        return self.get_emendas(**kwargs)

    @action(
        methods=[
            "post",
        ],
        detail=True,
        permission_classes=(AgrupamentoPermission,),
    )
    def devolver_emenda(self, request, *args, **kwargs):
        """Devolve a emenda para correção pela tela do agrupamento (LOA-AGR-091 a 095)."""
        from cmj.api.loa.views.agrupamentoemendaloa import AgrupamentoEmendaLoaViewSet

        agrupamento = self.get_queryset().filter(id=kwargs["pk"]).first()
        if not agrupamento:
            return JsonResponse({"detail": "Agrupamento não encontrado."}, status=404)
        try:
            emenda = EmendaLoa.objects.filter(pk=int(request.data["emendaloa"])).first()
        except (KeyError, TypeError, ValueError):
            emenda = None
        if not emenda:
            raise DRFValidationError("Emenda Impositiva não encontrada.")

        try:
            saiu = Agrupamento.service.devolver_emenda(
                request.user, agrupamento, emenda
            )
        except PermissionDenied as e:
            raise DRFPermissionDenied(str(e))
        except ValidationError as e:
            raise DRFValidationError(e.messages)

        dados = {
            "detail": "Emenda devolvida para correção com sucesso.",
            "saiu_do_agrupamento": saiu,
            "aviso_finalidade": "",
        }
        if saiu:
            # LOA-AGR-092: como na lixeira, a finalidade é gerada de novo sem a emenda
            dados["aviso_finalidade"] = (
                AgrupamentoEmendaLoaViewSet.atualizar_finalidade(agrupamento)
            )
            dados["agrupamento_finalidade"] = agrupamento.finalidade
        return Response(dados)

    @wrapper_queryset_response_for_drf_action(model=EmendaLoa)
    def get_emendas(self, **kwargs):
        self.serializer_class = EmendaLoaSearchSerializer
        qs = self.get_queryset()
        # remove filtro padrão de fase do EmendaLoaManager, que filtra apenas fases maiores que 0
        qs = qs.model._base_manager.all()
        return qs.filter(
            agrupamentoemendaloa__agrupamento_id=kwargs["pk"]
        ).select_related("agrupamentoemendaloa__agrupamento")

    @action(
        methods=[
            "post",
        ],
        detail=True,
        permission_classes=(AgrupamentoPermission,),
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
        permission_classes=(AgrupamentoPermission,),
    )
    def generate_finalidade_global(self, request, *args, **kwargs):
        agrupamento = self.get_queryset().filter(id=kwargs["pk"]).first()
        finalidade_global = ""
        try:
            if agrupamento:
                agrupamento.update_finalidade_com_ia(forcar=True)
                finalidade_global = agrupamento.finalidade
            return JsonResponse({"finalidade_global": finalidade_global})
        except (ValueError, IAEmentaEmendaColetivaError) as e:
            # responder com erro para que o promise no frontend saiba que houve falha
            return JsonResponse({"error": str(e)}, status=400)

    @action(
        methods=[
            "post",
        ],
        detail=True,
        permission_classes=(AgrupamentoPermission,),
    )
    def gerar_emenda_coletiva(self, request, *args, **kwargs):
        agrupamento = self.get_queryset().filter(id=kwargs["pk"]).first()
        if not agrupamento:
            return JsonResponse({"error": "Agrupamento not found"}, status=404)

        try:
            emendas_criadas = agrupamento.gerar_emendas_coletivas(user=request.user)
            # após gerar emendas coletivas, atualizar a instância para refletir as mudanças
            return JsonResponse(
                {
                    "status": "success",
                    "emendas_criadas": [e.id for e in emendas_criadas],
                }
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    @action(
        methods=[
            "post",
        ],
        detail=True,
        permission_classes=(AgrupamentoPermission,),
    )
    def cancelar_emendas_coletivas(self, request, *args, **kwargs):
        agrupamento = self.get_queryset().filter(id=kwargs["pk"]).first()
        if not agrupamento:
            return JsonResponse({"error": "Agrupamento not found"}, status=404)

        try:
            # LOA-AGR-072: exclui as coletivas e devolve -10 e 17 para 15 (no model)
            excluidas, devolvidas = agrupamento.cancelar_emendas_coletivas(
                user=request.user
            )

            return JsonResponse(
                {
                    "status": "success",
                    "coletivas_excluidas": excluidas,
                    "emendas_devolvidas": devolvidas,
                }
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    @action(
        methods=[
            "get",
        ],
        detail=True,
        permission_classes=(AgrupamentoEditorPermission,),
    )
    def view(self, request, *args, **kwargs):
        base_url = pdf_base_url(request)  # LOA-LST-086

        agrupamento = self.get_object()
        emendas_coletivas_structured = agrupamento.preparar_dados_para_coletiva(
            for_preview=True
        )

        p = int(request.GET.get("p", "0"))
        doc = pymupdf.Document()
        for idx, emenda_coletiva in enumerate(emendas_coletivas_structured):
            self._art = 0
            context = {}
            context["lineHeight"] = 1.2
            context["view"] = self
            context["agrupamento"] = emenda_coletiva

            context["model"] = request.GET.get("model", "1")
            if not context["model"].isdigit():
                context["model"] = "1"

            """
            - model = 1 - padrão
                - campo finalidade_customizada tem precedência sobre finalidade_automatica e
                  é colocado tanto na ementa quanto no art 1º
                - o detalhamento dos objetos das emendas individuais são colocados junto ao parlamentar

            - model = 2 - finalidade_automatica e finalidade_customizada não aparecem na ementa e no Art 1º

            - model = 3 - remove finalidade_customizada e finalidade_automatica do Art 1.

            - model = 4 - remove detalhamento dos objetos das emendas individuais do Art 1.
            """

            if context["model"] == "2":
                emenda_coletiva["finalidade_automatica"] = ""
                emenda_coletiva["finalidade_customizada"] = ""

            template = render_to_string("loa/pdf/agrupamento_preview.html", context)
            pdf_file = make_pdf(base_url=base_url, main_template=template)

            doc_individual = pymupdf.Document(stream=pdf_file)
            emenda_coletiva["doc"] = doc_individual
            doc.insert_pdf(doc_individual)

        if not doc.page_count:
            # cria uma página e escreve "Nenhuma página gerada. "
            page = doc.new_page()

            total_emendas_agrupamento = agrupamento.emendas.count()
            texto = f"""
                Nenhuma Emenda gerada.
                Total de emendas no agrupamento: {total_emendas_agrupamento}
                Com permissão de junção em Emenda Coletiva: {len(emendas_coletivas_structured)}
            """

            page.insert_text((72, 72), texto, fontsize=12)
            # bresponse = doc.write()
            # return HttpResponse(
            #     bresponse, content_type="application/pdf", status=400
            # )
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
            agrupamento.loa.ano,
            agrupamento.id,
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
