from copy import deepcopy
from datetime import datetime
import glob
import logging
from operator import attrgetter
import os
import tempfile
import zipfile

from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, F
from django.db.models.aggregates import Max
from django.db.models.deletion import ProtectedError
from django.http.response import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
import fitz
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from cmj.arq import tasks
from cmj.arq.models import DraftMidia, Draft
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
from sapl.api.mixins import ResponseFileMixin
from sapl.utils import hash_sha512


logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('arq')
    ]
)


@customize(Draft)
class _Draft:
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        qs = qs.filter(owner=self.request.user)
        return qs

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    'message': _('Não é possível excluir um Draft que possui mídia.')
                }
            )

    def create(self, request, *args, **kwargs):
        def get_serializer(*args, **kwargs):
            kwargs['data'].update({'owner': self.request.user.id})
            serializer = super(type(self), self).get_serializer(
                *args, **kwargs)
            return serializer
        self.get_serializer = get_serializer
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['POST'])
    def uploadfiles(self, request, *args, **kwargs):

        try:
            draft = Draft.objects.get(pk=kwargs['pk'])
        except:
            raise NotFound('Draft não encontrado!')

        smax = DraftMidia.objects.filter(
            draft=draft
        ).aggregate(
            smax=Max('sequencia')
        ).get('smax', 1) or 0

        lastmodified = request.POST.getlist('lastmodified')
        files = request.FILES.getlist('arquivos')

        for i, f in enumerate(files):
            files[i] = {
                'file': f,
                'lastmodified': lastmodified[i]
            }

        files = sorted(files, key=lambda f: f['file'].name)

        for seq, item in enumerate(files, start=smax + 1):
            f = item['file']
            dm = DraftMidia()
            dm.draft = draft
            dm.sequencia = seq
            dm.arquivo = f

            dm.metadata = {
                'uploadedfile': {
                    'name': f.name,
                    'paginas': 0
                },
                'ocrmypdf': {
                    'pdfa': False
                }
            }

            dm.save()

            if f.content_type != 'application/pdf':
                fname = f.name + '.pdf'
                doc = fitz.open()

                # open pic as document
                img = fitz.open(dm.arquivo.path)
                rect = img[0].rect  # pic dimension
                pdfbytes = img.convert_to_pdf()  # make a PDF stream
                img.close()  # no longer needed
                imgPDF = fitz.open("pdf", pdfbytes)  # open stream as PDF
                page = doc.new_page(width=rect.width,  # new page with ...
                                    height=rect.height)  # pic dimension
                page.show_pdf_page(rect, imgPDF, 0)  # image fills the page

                fpdf = dm.arquivo.path
                fpdf = fpdf + '.pdf'
                doc.save(fpdf)

                dm.arquivo.delete()

                dm.arquivo = fpdf
                dm.metadata['uploadedfile']['name'] = fname
                dm.metadata['uploadedfile']['paginas'] = 1
                dm.save()

            doc = fitz.open(dm.arquivo.file)
            dm.metadata['uploadedfile']['paginas'] = len(doc)
            dm.save()

            tasks.task_ocrmypdf.apply_async(
                (
                    dm._meta.app_label,
                    dm._meta.model_name,
                    'arquivo',
                    dm.id,
                ),
                countdown=10
            )

        serializer = self.get_serializer(draft)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def zipfile(self, request, *args, **kwargs):

        with tempfile.SpooledTemporaryFile(max_size=512000000) as tmp:

            with zipfile.ZipFile(tmp, 'w') as file:

                draft = Draft.objects.get(pk=kwargs['pk'])

                for dm in draft.draftmidia_set.all():
                    file.write(dm.arquivo.path,
                               dm.metadata['uploadedfile']['name'])

            tmp.seek(0)

            response = HttpResponse(tmp.read(),
                                    content_type='application/zip')

        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 0
        response['Content-Disposition'] = \
            'inline; filename=%s.zip' % (
                slugify(draft.descricao))

        return response


@customize(DraftMidia)
class _DraftMidia(ResponseFileMixin):

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)

    @action(detail=True)
    def expandir(self, request, *args, **kwargs):
        dm_atual = self.get_queryset().filter(pk=kwargs['pk']).first()
        dm_new = deepcopy(dm_atual)

        doc = fitz.open(dm_atual.arquivo.file)
        ldoc = len(doc)

        if ldoc <= 1:
            serializer = self.get_serializer(dm_atual)
            return Response(serializer.data)

        self.get_queryset().filter(
            draft_id=dm_atual.draft_id,
            sequencia__gt=dm_atual.sequencia
        ).update(sequencia=F('sequencia') + ldoc)

        for p in range(ldoc):

            d = fitz.open()
            d.insert_pdf(doc, from_page=p, to_page=p)

            fn = f'{str(dm_atual.arquivo.file)}-p{p+1:0>3}.pdf'

            d.save(fn)

            dm_new.id = None
            dm_new.arquivo = fn
            dm_new.sequencia = dm_atual.sequencia + p - 1
            dm_new.metadata['uploadedfile']['paginas'] = 1
            dm_new.metadata['uploadedfile']['name'] = fn.split('/')[-1]
            dm_new.metadata['ocrmypdf'] = {'pdfa': False}
            dm_new.save()

            tasks.task_ocrmypdf.apply_async(
                (
                    dm_new._meta.app_label,
                    dm_new._meta.model_name,
                    'arquivo',
                    dm_new.id,
                ),
                countdown=10 + p
            )

        dm_atual.delete()

        serializer = self.get_serializer(dm_new)
        return Response(serializer.data)

    @action(detail=True)
    def rotate(self, request, *args, **kwargs):
        dm = self.get_queryset().filter(pk=kwargs['pk']).first()
        p = int(request.GET.get('page', 1)) - 1
        angulo = int(request.GET.get('angulo', 90))

        dm.clear_cache(page=p)

        doc = fitz.open(dm.arquivo.path)
        nd = fitz.open()
        lp = len(doc)
        if p:
            nd.insert_pdf(doc, from_page=0, to_page=p - 1)

        nd.insert_pdf(doc, from_page=p, to_page=p,
                      rotate=doc[p].rotation + angulo)
        if p != lp - 1:
            nd.insert_pdf(doc, from_page=p + 1, to_page=lp - 1)
        nd.save(doc.name)
        nd.close()
        doc.close()

        serializer = self.get_serializer(dm)
        return Response(serializer.data)

    @action(detail=True)
    def delete_page(self, request, *args, **kwargs):
        dm = self.get_queryset().filter(pk=kwargs['pk']).first()
        p = int(request.GET.get('page', 1)) - 1

        dm.clear_cache(page=p)

        doc = fitz.open(dm.arquivo.path)
        nd = fitz.open()
        lp = len(doc)

        if p:
            nd.insert_pdf(doc, from_page=0, to_page=p - 1)

        nd.save(doc.name)
        nd.close()
        doc.close()

        serializer = self.get_serializer(dm)
        return Response(serializer.data)
