import logging
from decimal import Decimal

import pymupdf
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.http.response import HttpResponse
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from cmj.api.forms import EmendaLoaFilterSet
from cmj.api.loa.serializers import EmendaLoaSearchSerializer
from cmj.loa.models import EmendaLoa, EmendaLoaParlamentar, Empenho
from cmj.utils.utils_report import pdf_base_url
from sapl.api.permissions import SaplModelPermissions

logger = logging.getLogger(__name__)


class EmendaLoaViewSet:

    class EmendaLoaPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            has_perm = super().has_permission(request, view)

            has_permission_custom = None
            method = request.method.lower()
            if hasattr(self, f"has_permission_{method}"):
                has_permission_custom = getattr(self, f"has_permission_{method}")

            if has_perm and not has_permission_custom:
                return has_perm

            u = request.user
            if u.is_anonymous:
                return False

            if has_permission_custom:
                return has_permission_custom(request, view)

            if request.method == "POST":
                # LOA-EMD-082: operador de autor cria, publicada ou não a LOA
                return EmendaLoa.service.pode_criar(u)

            elif request.method == "PATCH":

                el = EmendaLoa.objects.get(pk=view.kwargs["pk"])

                # LOA-EMD-005 e LOA-EMD-076: só o autor do dono edita; coautores
                # só consultam
                return EmendaLoa.service.pode_editar(u, el)

            return False

    permission_classes = (EmendaLoaPermission,)
    filterset_class = EmendaLoaFilterSet

    def get_queryset(self):
        qs = super().get_queryset()
        # LOA-LST-083: a consulta segue a visibilidade da listagem; a escrita
        # continua decidida pelas permissões de edição
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            qs = EmendaLoa.service.visiveis(self.request.user, qs)
        return qs

    @staticmethod
    def fase_do_request(request, default=None):
        fase = request.data.get("fase", default)
        if fase is None:
            return None
        try:
            return int(fase)
        except (TypeError, ValueError):
            raise DRFValidationError("Fase inválida.")

    def create(self, request, *args, **kwargs):
        fase = self.fase_do_request(request, default=EmendaLoa.PROPOSTA)
        if not EmendaLoa.criacao_permitida(request.user, fase):
            raise DRFValidationError(
                "A Emenda Impositiva só pode ser criada na fase "
                f'"{dict(EmendaLoa.FASE_CHOICE)[EmendaLoa.PROPOSTA]}".'
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        destino = self.fase_do_request(request)
        if destino is not None:
            el = self.get_object()
            if not EmendaLoa.transicao_permitida(request.user, el.fase, destino):
                fases = dict(EmendaLoa.FASE_CHOICE)
                raise DRFValidationError(
                    "Você não tem permissão para mudar a fase de "
                    f'"{fases.get(el.fase, el.fase)}" para "{fases.get(destino, destino)}".'
                )
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        el = serializer.save()
        # LOA-FASE-067: o serializer cria a instância, então o signal grava o histórico
        # inicial sem usuário; logo após a criação ele é o único registro.
        el.emendaloahistoricofase_set.filter(usuario__isnull=True).update(
            usuario=self.request.user
        )

    def perform_update(self, serializer):
        # LOA-EMD-071: `owner` é mantido pelo servidor e não chega aos dados
        # validados; enviado no PATCH, entra na conferência para ser recusado
        dados = dict(serializer.validated_data)
        if "owner" in self.request.data:
            dados["owner"] = self.request.data["owner"]

        # LOA-EMD-070 a 073: só os campos que o perfil pode alterar
        try:
            EmendaLoa.service.validar_alteracao(
                self.request.user, serializer.instance, dados
            )
        except ValidationError as e:
            raise DRFValidationError(e.messages)

        # LOA-EMD-083: sem campo do model no PATCH, a emenda não é gravada, o que
        # evita signals e o sync() (LOA-EMD-031) sem mudança real
        if not serializer.validated_data:
            return

        serializer.instance._usuario_fase = self.request.user  # LOA-FASE-067
        serializer.save()

    @action(
        methods=[
            "patch",
        ],
        detail=True,
    )
    def update_parlassinantes(self, request, *args, **kwargs):

        data = request.data
        data["emendaloa_id"] = kwargs["pk"]
        dchecked = data.pop("checked")

        el = EmendaLoa.objects.get(pk=kwargs["pk"])

        # LOA-EMD-077 a 079: perfil, parlamentar da LOA e parlamentar do dono
        try:
            EmendaLoa.service.validar_parlamentares(
                request.user,
                el,
                {data["parlamentar_id"]: Decimal("1.00") if dchecked else None},
            )
        except ValidationError as e:
            raise DRFValidationError(e.messages)

        pselected = el.loa.parlamentares.filter(id=data["parlamentar_id"]).first()
        if not dchecked:
            el.parlamentares.remove(pselected)
        else:
            el.parlamentares.add(pselected)
        el.save()

        serializer = self.get_serializer(el)
        return Response(serializer.data)

    @action(
        methods=[
            "patch",
        ],
        detail=True,
    )
    def updatevaloremenda(self, request, *args, **kwargs):
        # instance = self.get_object()

        data = request.data
        obj = data.pop("valor")
        try:
            if obj and "." in obj and "," in obj:
                if obj.rindex(",") > obj.rindex("."):
                    obj = obj.replace(".", "").replace(",", ".")
                else:
                    obj = obj.replace(",", "")
            elif obj and "," in obj:
                obj = obj.replace(",", ".")

            obj = Decimal(obj)
        except:
            obj = Decimal("0.01")

        el = EmendaLoa.objects.get(pk=kwargs["pk"])

        # LOA-EMD-074: Valor Global só para quem pode alterar o campo valor
        try:
            EmendaLoa.service.validar_alteracao(request.user, el, {"valor": obj})
        except ValidationError as e:
            raise DRFValidationError(e.messages)

        el.valor = obj
        el.save()

        serializer = self.get_serializer(el)
        return Response(serializer.data)

    @action(
        methods=[
            "patch",
        ],
        detail=True,
    )
    def updatevalorparlamentar(self, request, *args, **kwargs):
        # instance = self.get_object()

        data = request.data
        data["emendaloa_id"] = kwargs["pk"]
        obj = data.pop("valor")
        try:
            if obj and "." in obj and "," in obj:
                if obj.rindex(",") > obj.rindex("."):
                    obj = obj.replace(".", "").replace(",", ".")
                else:
                    obj = obj.replace(",", "")
            elif obj and "," in obj:
                obj = obj.replace(",", ".")

            obj = Decimal(obj)
        except:
            obj = Decimal("0.00")

        # LOA-EMD-077 a 079: perfil, parlamentar da LOA e parlamentar do dono
        try:
            EmendaLoa.service.validar_parlamentares(
                request.user,
                EmendaLoa.objects.get(pk=kwargs["pk"]),
                {data["parlamentar_id"]: obj},
            )
        except ValidationError as e:
            raise DRFValidationError(e.messages)

        elp, created = EmendaLoaParlamentar.objects.get_or_create(**data)
        elp.valor = obj
        elp.save()
        el = elp.emendaloa

        if not elp.valor:
            elp.delete()

        el.save()

        serializer = self.get_serializer(el)

        return Response(serializer.data)

    @action(detail=True)
    def view(self, request, *args, **kwargs):
        base_url = pdf_base_url(request)  # LOA-LST-086

        el = self.get_object()
        el_changed = False
        if "style" not in el.metadata:
            el.metadata["style"] = {"lineHeight": 150, "espacoAssinatura": 0}
            el_changed = True

        # LOA-EMD-085: só quem pode editar a emenda grava o estilo; os demais
        # recebem o documento com o estilo gravado
        pode_gravar = EmendaLoa.service.pode_editar(request.user, el)

        if pode_gravar and "lineHeight" in request.GET:
            lineHeight = float(el.metadata["style"]["lineHeight"])
            lineHeight = min(300, int(request.GET.get("lineHeight", lineHeight)))
            lineHeight = max(100, lineHeight)

            if lineHeight != el.metadata["style"]["lineHeight"]:
                el.metadata["style"]["lineHeight"] = lineHeight
                el_changed = True

        if pode_gravar and "espacoAssinatura" in request.GET:
            if "espacoAssinatura" not in el.metadata["style"]:
                el.metadata["style"]["espacoAssinatura"] = 0
                el_changed = True

            espacoAssinatura = int(el.metadata["style"].get("espacoAssinatura", 0))
            espacoAssinatura = (
                1 if request.GET.get("espacoAssinatura", 0) == "true" else 0
            )

            if espacoAssinatura != el.metadata["style"].get("espacoAssinatura", 0):
                el.metadata["style"]["espacoAssinatura"] = espacoAssinatura
                el_changed = True

        if el_changed and pode_gravar:
            el.save()

        try:
            p = int(request.GET.get("page", 0))
        except:
            p = 0

        pdf_file = EmendaLoa.service.documento_pdf(el, base_url)
        ext = "pdf"

        doc = pymupdf.Document(stream=pdf_file)

        if p:
            d2b = doc
            ext = "png"
            p -= 1
            page = doc[p % len(doc)]
            d2b = page.get_pixmap(dpi=300)

            bresponse = d2b.tobytes()
            doc.close()
        else:
            bresponse = doc.tobytes()

        arcname = EmendaLoa.service.nome_documento(el, f"-p{p+1}" if p else "", ext)

        response = HttpResponse(
            bresponse, content_type="image/png" if p else "application/pdf"
        )
        response["Content-Disposition"] = f'inline; filename="{arcname}"'
        response["Cache-Control"] = "no-cache"
        response["Pragma"] = "no-cache"
        response["Expires"] = 0
        return response

    @action(
        methods=[
            "get",
        ],
        detail=True,
    )
    def totais(self, request, *args, **kwargs):
        r = self.get_object().totais_contabeis
        r = {k: formats.number_format(v, force_grouping=True) for k, v in r.items()}

        return Response(r)

    @action(detail=False)
    def search(self, request, *args, **kwargs):
        # TODO: refatorar para usar filterset e o serializer de listagem, ao invés de criar um serializer específico para a busca e uma função de filtro específica
        def filter_queryset(qs):
            ano = request.GET.get("ano", None)
            tipo = request.GET.get("tipo", None)
            query = request.GET.get("q", "")
            query = query.split(" ")

            q = Q()
            for termo in query:
                q &= Q(search__unaccent__icontains=termo)

            qs = qs.filter(fase__lt=EmendaLoa.LIBERACAO_CONTABIL, loa__ano=ano)
            if tipo is not None:
                qs = qs.filter(tipo=tipo)
            if query:
                qs = qs.filter(q)

            return qs.order_by(
                "-tipo",
                "-agrupamentoemendaloa",
                "unidade__especificacao",
                "entidade",
                "-fase",
            )

        self.serializer_class = EmendaLoaSearchSerializer
        self.filter_queryset = filter_queryset

        return self.list(request, *args, **kwargs)

    @action(detail=False)
    def totalize_empenhos(self, request, pk=None):
        def filter_queryset():
            qs = self.filter_queryset(self.get_queryset())
            return qs

        qs = filter_queryset()
        empenho_ids = qs.values_list(
            "empenhoemendaajuste_set__empenho_id", flat=True
        ).distinct()
        totals = Empenho.objects.filter(id__in=empenho_ids).aggregate(
            total_empenhado=Sum("valor_empenhado"),
            total_liquidado=Sum("valor_liquidado"),
            total_pago_bruto=Sum("valor_pago_bruto"),
            total_anulado=Sum("valor_anulado"),
        )

        return Response(totals)
