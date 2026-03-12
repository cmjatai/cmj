import logging
from decimal import Decimal

import pymupdf
from django.db.models import Q
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.utils import formats
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.response import Response

from cmj.api.forms import EmendaLoaFilterSet
from cmj.api.serializers import CmjSerializerMixin
from cmj.loa.models import EmendaLoa, EmendaLoaParlamentar, Loa
from cmj.utils_report import make_pdf
from sapl.api.permissions import SaplModelPermissions
from sapl.parlamentares.models import Parlamentar

logger = logging.getLogger(__name__)


class EmendaLoaSearchSerializer(CmjSerializerMixin):

    str_valor = SerializerMethodField()
    str_parlamentares = SerializerMethodField()

    finalidade = SerializerMethodField()

    str_fase = SerializerMethodField()

    class Meta(CmjSerializerMixin.Meta):
        model = EmendaLoa

    def get_finalidade(self, obj):
        return obj.finalidade_format

    def get_str_fase(self, obj):
        return obj.get_fase_display()

    def get_str_valor(self, obj):
        return formats.number_format(obj.valor, force_grouping=True)

    def get_str_parlamentares(self, obj):
        elps = obj.emendaloaparlamentar_set.all()

        r = []
        for elp in elps:
            r.append(str(elp))
        return r


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

                data = request.data

                if "loa" in data:
                    loa = Loa.objects.get(pk=data["loa"])

                if not has_perm:
                    return u.operadorautor_set.exists() and not loa.publicado

            elif request.method == "PATCH":

                el = EmendaLoa.objects.get(pk=view.kwargs["pk"])

                participa = False
                fase = True
                if u.operadorautor_set.exists():
                    parlamentar = u.operadorautor_set.first().autor.autor_related
                    if isinstance(parlamentar, Parlamentar):
                        participa = el.emendaloaparlamentar_set.filter(
                            parlamentar=parlamentar
                        ).exists()

                        if (
                            el.fase > EmendaLoa.PROPOSTA_LIBERADA
                            and el.fase != EmendaLoa.LIBERACAO_CONTABIL
                        ):
                            fase = False

                return (u.has_perm("loa.emendaloa_full_editor") and not el.materia) or (
                    u.operadorautor_set.exists()
                    and not el.materia
                    and participa
                    and fase
                )

            return False

    permission_classes = (EmendaLoaPermission,)
    filterset_class = EmendaLoaFilterSet

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

        pselected = el.loa.parlamentares.filter(id=data["parlamentar_id"]).first()
        if not dchecked:
            u = request.user
            if not u.is_superuser and u.operadorautor_set.exists():
                puser = u.operadorautor_set.first().autor.autor_related

                if puser == pselected:
                    raise DRFValidationError(
                        "Você não pode remover o Parlamentar "
                        "ao qual seu usuário está ligado. "
                        "Caso queira, você pode excluir esse registro "
                        "clicando em excluir na tela de consulta."
                    )
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

        u = request.user
        if not u.is_superuser and u.operadorautor_set.exists():
            p = u.operadorautor_set.first().autor.autor_related

            if p.id == int(data["parlamentar_id"]) and obj <= Decimal("0.00"):
                raise DRFValidationError(
                    "Você não pode zerar o Valor do Parlamentar "
                    "ao qual seu usuário está ligado. "
                    "Caso queira, você pode excluir esse registro "
                    "clicando em excluir na tela de consulta."
                )

        elp, created = EmendaLoaParlamentar.objects.get_or_create(**data)
        elp.valor = obj
        elp.save()
        el = elp.emendaloa

        if not elp.valor:
            elp.delete()

        el.save()

        serializer = self.get_serializer(el)

        return Response(serializer.data)

    @property
    def art(self):
        if not hasattr(self, "_art"):
            self._art = 0

        self._art += 1
        return self._art

    @action(detail=True)
    def view(self, request, *args, **kwargs):
        # base_url = settings.MEDIA_ROOT if settings.DEBUG else request.build_absolute_uri()
        base_url = request.build_absolute_uri()

        el = self.get_object()
        el_changed = False
        if "style" not in el.metadata:
            el.metadata["style"] = {"lineHeight": 150, "espacoAssinatura": 0}
            el_changed = True

        if "lineHeight" in request.GET:
            lineHeight = float(el.metadata["style"]["lineHeight"])
            lineHeight = min(300, int(request.GET.get("lineHeight", lineHeight)))
            lineHeight = max(100, lineHeight)

            if lineHeight != el.metadata["style"]["lineHeight"]:
                el.metadata["style"]["lineHeight"] = lineHeight
                el_changed = True

        if "espacoAssinatura" in request.GET:
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

        if el_changed:
            el.save()

        context = {
            "view": self,
            "object": el,
            "lineHeight": str(el.metadata["style"]["lineHeight"] / 100.0),
            "espacoAssinatura": str(
                el.metadata["style"].get("espacoAssinatura", "") or ""
            ),
        }

        try:
            p = int(request.GET.get("page", 0))
        except:
            p = 0

        template = render_to_string("loa/pdf/emendaloa_preview.html", context)
        pdf_file = make_pdf(base_url=base_url, main_template=template)
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

        nome_autor = el.owner.operadorautor_set.first() or ""
        if nome_autor:
            nome_autor = nome_autor.autor.nome

        arcname = "{}-{}-{:04d}-{}{}.{}".format(
            el.loa.ano,
            slugify(nome_autor),
            el.id,
            slugify(el.get_tipo_display()),
            f"-p{p+1}" if p else "",
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

        def filter_queryset(qs):
            ano = request.GET.get("ano", None)
            query = request.GET.get("q", "")
            query = query.split(" ")

            q = Q()
            for termo in query:
                q &= Q(search__unaccent__icontains=termo)

            qs = qs.filter(fase__lt=EmendaLoa.LIBERACAO_CONTABIL, loa__ano=ano)
            if query:
                qs = qs.filter(q)

            return qs.order_by("-fase")

        self.serializer_class = EmendaLoaSearchSerializer
        self.filter_queryset = filter_queryset

        return self.list(request, *args, **kwargs)
