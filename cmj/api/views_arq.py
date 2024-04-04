from copy import deepcopy
from datetime import datetime
import glob
import logging
from operator import attrgetter
import os
import re
from subprocess import TimeoutExpired, CalledProcessError
import subprocess
import tempfile
import zipfile

from PIL import Image, ImageSequence
from django.apps.registry import apps
from django.conf import settings
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
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from cmj.api.serializers import DraftMidiaSerializer, ArqClasseSerializer,\
    ArqDocSerializer
from cmj.arq import tasks
from cmj.arq.models import DraftMidia, Draft, ArqClasse, ArqDoc
from cmj.globalrules import GROUP_ARQ_OPERADOR
from cmj.settings.project import DEBUG
from cmj.utils import TIPOS_IMG_PERMITIDOS, TIPOS_MIDIAS_PERMITIDOS
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize
import sapl
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

        draft = Draft.objects.get(pk=kwargs['pk'])

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
            tipo = TIPOS_MIDIAS_PERMITIDOS.get(f.content_type, None)

            if tipo not in ('pdf', 'jpg', 'png',
                            'doc', 'docx', 'odt',
                            'xls', 'xlsx', 'ods',
                            'tif', 'tiff'):
                raise ValidationError(
                    _('Os arquivos possíveis de envio são do tipo: PDF, JPG, PNG, ODT, DOC, DOCX, ODS, XLS, XLSX, TIF, TIFF'))

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
                    'pdfa': DraftMidia.METADATA_PDFA_NONE
                }
            }

            dm.save()

            if tipo in ('jpg', 'png'):
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

                dm.arquivo = fpdf[len(settings.MEDIA_ROOT) + 1:]
                dm.metadata['uploadedfile']['name'] = fname
                dm.metadata['uploadedfile']['paginas'] = 1
                dm.save()
            elif tipo in ('tiff',):

                fname = dm.arquivo.path.split('/')[-1] + '.pdf'

                tiff_path = dm.arquivo.path

                fpdf = tiff_path.replace('.tiff', '.pdf')
                fpdf = tiff_path.replace('.tif', '.pdf')

                image = Image.open(tiff_path)

                images = []
                for i, page in enumerate(ImageSequence.Iterator(image)):
                    page = page.convert("RGB")
                    images.append(page)
                if len(images) == 1:
                    images[0].save(fpdf)
                else:
                    images[0].save(fpdf, save_all=True,
                                   append_images=images[1:])

                dm.arquivo.delete()

                dm.arquivo = fpdf[len(settings.MEDIA_ROOT) + 1:]
                dm.metadata['uploadedfile']['name'] = fname
                dm.metadata['uploadedfile']['paginas'] = len(images)
                dm.save()

            elif tipo in ('doc', 'docx', 'odt', 'xls', 'xlsx', 'ods'):
                fpdf = '/'.join(dm.arquivo.path.split('/')[:-1])
                fname = dm.arquivo.path.split('/')[-1]
                fname = re.sub(f'{tipo}$', 'pdf', fname)

                cmd = [
                    'lowriter',
                    '--headless',
                    '--convert-to',
                    'pdf:draw_pdf_Export:{"SelectPdfVersion":{"type":"long","value":"2"}}',
                    '--outdir', fpdf,
                    str(dm.arquivo.path)
                ]
                try:
                    subprocess.run(cmd, check=True, timeout=60)
                except TimeoutExpired:
                    logger.error('Timeout na converserção de arquivo')
                    raise ValidationError('Timeout na converserção de arquivo')

                except CalledProcessError:
                    logger.error('Erro na execução de conversão de arquivo')
                    raise ValidationError(
                        'Erro na execução de conversão de arquivo')
                else:
                    logger.info('Arquivo convertido!')

                    dm.arquivo.delete()

                    fpdf = f'{fpdf}/{fname}'

                    dm.arquivo = fpdf[len(settings.MEDIA_ROOT) + 1:]
                    dm.metadata['uploadedfile']['name'] = fname
                    dm.metadata['uploadedfile']['paginas'] = 1
                    dm.save()

            doc = fitz.open(dm.arquivo.file)
            dm.metadata['uploadedfile']['paginas'] = len(doc)
            dm.save()
            doc.close()

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

    @action(detail=True, methods=['GET'])
    def unirmidias(self, request, *args, **kwargs):

        try:
            draft = Draft.objects.get(pk=kwargs['pk'])
        except:
            raise NotFound('Draft não encontrado!')

        dm_draft = list(draft.draftmidia_set.all())

        if len(dm_draft) <= 1:
            serializer = self.get_serializer(draft)
            return Response(serializer.data)

        dm_primary = dm_draft[0]
        fp = dm_primary.arquivo.path.split('/')[:-1]
        fname = f'{dm_primary.id:09}.pdf'
        fp = f'{"/".join(fp)}/{fname}'

        d_new = fitz.open()
        for dm in dm_draft:
            doc = fitz.open(dm.arquivo.file)
            d_new.insert_pdf(doc, from_page=0, to_page=len(doc))
            doc.close()

        d_new.metadata['title'] = draft.descricao
        d_new.metadata['producer'] = 'PortalCMJ'
        d_new.set_metadata(d_new.metadata)
        d_new.save(fp, garbage=3, clean=True, deflate=True)

        #pdf = Pdf.new()
        # for dm in dm_draft:
        #    doc = Pdf.open(dm.arquivo.file)
        #    pdf.pages.extend(doc.pages)
        #    doc.close()
        # pdf.save(fp)

        dm_primary.metadata['uploadedfile']['name'] = fname
        dm_primary.metadata['uploadedfile']['paginas'] = len(d_new)
        dm_primary.metadata['ocrmypdf'] = {
            'pdfa': DraftMidia.METADATA_PDFA_NONE}

        dm_primary.clear_cache()
        fp_relative = fp[len(settings.MEDIA_ROOT) + 1:]
        if fp_relative != dm_primary.arquivo.name:
            dm_primary.arquivo.delete()
            dm_primary.arquivo = fp_relative
        dm_primary.sequencia = 1
        dm_primary.save()

        for dm in dm_draft[1:]:
            dm.delete()

        serializer = self.get_serializer(draft)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def cancela_pdf2pdfa(self, request, *args, **kwargs):

        try:
            draft = Draft.objects.get(pk=kwargs['pk'])
        except:
            raise NotFound('Draft não encontrado!')

        dms = draft.draftmidia_set.filter(
            metadata__ocrmypdf__pdfa=DraftMidia.METADATA_PDFA_AGND)

        for dm in dms:
            dm.metadata['ocrmypdf'] = {
                'pdfa': DraftMidia.METADATA_PDFA_NONE}
            dm.save()

        serializer = self.get_serializer(draft)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def pdf2pdfa(self, request, *args, **kwargs):

        try:
            draft = Draft.objects.get(pk=kwargs['pk'])
        except:
            raise NotFound('Draft não encontrado!')

        dms = draft.draftmidia_set.filter(
            metadata__ocrmypdf__pdfa=DraftMidia.METADATA_PDFA_NONE)

        dms_id = []
        for dm in dms:
            dms_id.append(dm.id)
            dm.metadata['ocrmypdf'] = {
                'pdfa': DraftMidia.METADATA_PDFA_AGND}
            dm.save()

        jobs = 4

        if request.user.groups.filter(name=GROUP_ARQ_OPERADOR).exists():
            jobs = 8

        params_task = (
            DraftMidia._meta.app_label,
            DraftMidia._meta.model_name,
            'arquivo',
            dms_id,
            jobs,
            False
        )

        if not DEBUG or (DEBUG and settings.FOLDER_DEBUG_CONTAINER == settings.PROJECT_DIR):
            tasks.task_ocrmypdf.apply_async(
                params_task,
                countdown=5
            )
        else:
            tasks.task_ocrmypdf_function(*params_task[:-1])

        serializer = self.get_serializer(draft)
        return Response(serializer.data)


@customize(DraftMidia)
class _DraftMidia(ResponseFileMixin):
    serializer_class = DraftMidiaSerializer

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)

    @action(detail=True)
    def decompor(self, request, *args, **kwargs):
        dm_atual = self.get_queryset().filter(pk=kwargs['pk']).first()
        dm_new = deepcopy(dm_atual)

        doc = fitz.open(dm_atual.arquivo.file)
        ldoc = len(doc)
        #doc = Pdf.open(dm_atual.arquivo.file)
        #ldoc = len(doc.pages)

        if ldoc < 1:
            serializer = self.get_serializer(dm_atual)
            return Response(serializer.data)

        self.get_queryset().filter(
            draft_id=dm_atual.draft_id,
            sequencia__gt=dm_atual.sequencia
        ).update(sequencia=F('sequencia') + ldoc)

        for p in range(ldoc):
            # for p, page in enumerate(doc.pages):

            fn = f'{str(dm_atual.arquivo.file)}'
            fn = fn[0: fn.rindex('.pdf')]
            fn = f'{fn}-p{p+1:0>3}.pdf'

            d = fitz.open()
            d.insert_pdf(doc, from_page=p, to_page=p)
            d.metadata['title'] = f'{dm_atual.draft.descricao} - página: {p+1}'
            #d.metadata['creator'] = str(request.user)
            d.metadata['producer'] = 'PortalCMJ'
            #d.metadata['creationDate'] = str(timezone.now())
            d.set_metadata(d.metadata)
            d.save(fn, garbage=3, clean=True, deflate=True)
            d.close()
            #dst = Pdf.new()
            # dst.pages.append(page)
            # dst.save(fn)

            dm_new.id = None
            dm_new.arquivo = fn[len(settings.MEDIA_ROOT) + 1:]
            dm_new.sequencia = dm_atual.sequencia + p
            dm_new.metadata['uploadedfile']['paginas'] = 1
            dm_new.metadata['uploadedfile']['name'] = fn.split('/')[-1]
            dm_new.metadata['ocrmypdf'] = {
                'pdfa': DraftMidia.METADATA_PDFA_NONE}
            dm_new.save()

        dm_atual.delete()

        serializer = self.get_serializer(dm_new)
        return Response(serializer.data)

    @action(detail=True)
    def pdf2pdfa(self, request, *args, **kwargs):
        dm = self.get_queryset().filter(pk=kwargs['pk']).first()
        dm.metadata['ocrmypdf'] = {'pdfa': DraftMidia.METADATA_PDFA_AGND}
        dm.save()

        params_task = (
            DraftMidia._meta.app_label,
            DraftMidia._meta.model_name,
            'arquivo',
            [dm.id, ],
            4,
            False
        )

        if not DEBUG or (DEBUG and settings.FOLDER_DEBUG_CONTAINER == settings.PROJECT_DIR):
            tasks.task_ocrmypdf.apply_async(
                params_task,
                countdown=5
            )
        else:
            tasks.task_ocrmypdf_function(*params_task[:-1])

        serializer = self.get_serializer(dm)
        return Response(serializer.data)

    @action(detail=True)
    def pdfacompact(self, request, *args, **kwargs):
        dm = self.get_queryset().filter(pk=kwargs['pk']).first()
        dm.metadata['ocrmypdf'] = {'pdfa': DraftMidia.METADATA_PDFA_AGND}
        dm.save()

        params_task = (
            DraftMidia._meta.app_label,
            DraftMidia._meta.model_name,
            'arquivo',
            [dm.id, ],
            2,
            True
        )

        if not DEBUG or (DEBUG and settings.FOLDER_DEBUG_CONTAINER == settings.PROJECT_DIR):
            tasks.task_ocrmypdf.apply_async(
                params_task,
                countdown=5
            )
        else:
            tasks.task_ocrmypdf_compact_function(*params_task[:-1])

        serializer = self.get_serializer(dm)
        return Response(serializer.data)

    @action(detail=True)
    def rotate(self, request, *args, **kwargs):
        dm = self.get_queryset().filter(pk=kwargs['pk']).first()
        p = int(request.GET.get('page', 1)) - 1
        angulo = int(request.GET.get('angulo', 90))

        dm.clear_cache(page=p + 1)

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

        dm.metadata['ocrmypdf'] = {'pdfa': DraftMidia.METADATA_PDFA_NONE}
        dm.save()

        serializer = self.get_serializer(dm)
        return Response(serializer.data)

    @action(detail=True)
    def delete_page(self, request, *args, **kwargs):
        dm = self.get_queryset().filter(pk=kwargs['pk']).first()
        p = int(request.GET.get('page', 1)) - 1

        dm.clear_cache(page=p + 1)

        doc = fitz.open(dm.arquivo.path)
        nd = fitz.open()
        lp = len(doc)

        if p:
            nd.insert_pdf(doc, from_page=0, to_page=p - 1)

        nd.save(doc.name)
        nd.close()
        doc.close()

        dm.metadata['ocrmypdf'] = {'pdfa': DraftMidia.METADATA_PDFA_NONE}
        dm.save()

        serializer = self.get_serializer(dm)
        return Response(serializer.data)


@customize(ArqClasse)
class _ArqClasse:
    serializer_class = ArqClasseSerializer

    def dispatch(self, request, *args, **kwargs):
        print(request.path)
        return super().dispatch(request, *args, **kwargs)


@customize(ArqDoc)
class _ArqDoc(ResponseFileMixin):
    serializer_class = ArqDocSerializer

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
