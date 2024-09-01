from decimal import Decimal
import logging

from django.apps.registry import apps
from django.conf import settings
from django.db.models import Q
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.utils.text import slugify
import pymupdf
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from cmj.loa.models import OficioAjusteLoa, EmendaLoa, Loa, EmendaLoaParlamentar,\
    DespesaConsulta, EmendaLoaRegistroContabil
from cmj.settings.medias import MEDIA_URL
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.mixins import ResponseFileMixin
from sapl.api.permissions import SaplModelPermissions
from sapl.base.models import CasaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.relatorios.views import make_pdf


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('loa')
    ]
)


@customize(OficioAjusteLoa)
class _OficioAjusteLoaViewSet(ResponseFileMixin):

    def custom_filename(self, item):
        arcname = '{}-{}.{}'.format(
            item.loa.ano,
            slugify(item.epigrafe),
            item.arquivo.path.split('.')[-1])
        return arcname

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)


@customize(EmendaLoa)
class _EmendaLoaViewSet:

    class EmendaLoaPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            has_perm = super().has_permission(request, view)

            if has_perm:
                return has_perm

            u = request.user
            if u.is_anonymous:
                return False

            if request.method == 'POST':
                if hasattr(self, 'has_permission_post'):
                    return self.has_permission_post(has_perm, u)

                data = request.data

                if 'loa' in data:
                    loa = Loa.objects.get(pk=data['loa'])

                if not has_perm:
                    return u.operadorautor_set.exists() and not loa.publicado

            elif request.method == 'PATCH':

                el = EmendaLoa.objects.get(pk=view.kwargs['pk'])

                participa = False
                if u.operadorautor_set.exists():
                    parlamentar = u.operadorautor_set.first().autor.autor_related
                    if isinstance(parlamentar, Parlamentar):
                        participa = el.emendaloaparlamentar_set.filter(
                            parlamentar=parlamentar).exists()

                return (
                    u.has_perm('loa.emendaloa_full_editor') and
                    not el.materia
                ) or (
                    u.operadorautor_set.exists() and
                    not el.materia and
                    participa
                )

            return False

    permission_classes = (EmendaLoaPermission, )

    @action(methods=['patch', ], detail=True)
    def updatevalorparlamentar(self, request, *args, **kwargs):

        #instance = self.get_object()

        data = request.data
        data['emendaloa_id'] = kwargs['pk']
        dvalor = data.pop('valor')
        try:
            valor = Decimal(dvalor)
        except:
            valor = Decimal('0.00')

        elp, created = EmendaLoaParlamentar.objects.get_or_create(**data)
        elp.valor = valor
        elp.save()
        el = elp.emendaloa

        if not elp.valor:
            elp.delete()

        el.atualiza_valor().save()

        serializer = self.get_serializer(el)

        return Response(serializer.data)

    @property
    def art(self):
        if not hasattr(self, '_art'):
            self._art = 0

        self._art += 1
        return self._art

    @action(detail=True)
    def preview(self, request, *args, **kwargs):
        #base_url = settings.MEDIA_ROOT if settings.DEBUG else request.build_absolute_uri()
        base_url = request.build_absolute_uri()

        el = self.get_object()

        if 'style' not in el.metadata:
            el.metadata['style'] = {'lineHeight': 150}
            el.save()

        if 'lineHeight' in request.GET:
            lineHeight = float(el.metadata['style']['lineHeight'])
            lineHeight = min(
                300, int(request.GET.get('lineHeight', lineHeight)))
            lineHeight = max(100, lineHeight)

            if lineHeight != el.metadata['style']['lineHeight']:
                el.metadata['style']['lineHeight'] = lineHeight
                el.save()

        context = {
            'view': self,
            'object': el,
            'lineHeight': str(el.metadata['style']['lineHeight'] / 100.0)
        }

        template = render_to_string('loa/pdf/emendaloa_preview.html', context)
        pdf_file = make_pdf(base_url=base_url, main_template=template)
        doc = pymupdf.Document(stream=pdf_file)

        try:
            p = int(request.GET.get('page', 0))
        except:
            p = 0

        d2b = doc
        if p:
            p -= 1
            page = doc[p % len(doc)]
            d2b = page.get_pixmap(dpi=300)

        bresponse = d2b.tobytes()
        doc.close()

        response = HttpResponse(
            bresponse, content_type='image/png' if p else 'application/pdf')
        return response


@customize(DespesaConsulta)
class _DespesaConsulta:

    @action(detail=False)
    def search(self, request, *args, **kwargs):

        def filter_queryset(qs):
            ano = request.GET.get('ano', None)
            query = request.GET.get('q', '')
            query = query.split(' ')

            q = Q()

            for termo in query:
                q &= (Q(codigo__icontains=termo) |
                      Q(especificacao__icontains=termo) |
                      Q(esp_orgao__icontains=termo) |
                      Q(esp_unidade__icontains=termo) |
                      Q(cod_natureza__icontains=termo))

            qs = qs.filter(loa__ano=ano)
            if query:
                qs = qs.filter(q)

            return qs
        self.filter_queryset = filter_queryset

        return self.list(request, *args, **kwargs)


@customize(EmendaLoaRegistroContabil)
class _EmendaLoaRegistroContabilViewSet:

    class EmendaLoaRegistroContabilPermission(_EmendaLoaViewSet.EmendaLoaPermission):
        def has_permission_post(self, has_perm, user):
            if has_perm:
                return has_perm

            return user.has_perm('loa.emendaloa_full_editor')

    permission_classes = (EmendaLoaRegistroContabilPermission, )
