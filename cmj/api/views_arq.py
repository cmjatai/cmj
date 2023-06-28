from datetime import datetime
import logging
from operator import attrgetter
import tempfile
import zipfile

from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.aggregates import Max
from django.db.models.deletion import ProtectedError
from django.http.response import HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
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
            dm.arquivo = f
            dm.sequencia = seq

            try:
                lm = datetime.fromtimestamp(int(item['lastmodified']))
            except:
                lm = datetime.fromtimestamp(int(item['lastmodified']) / 1000)

            dm.metadata = {
                'uploadedfile': {
                    'name': f.name,
                    'size': f.size,
                    'content_type': f.content_type,
                    'lastmodified': lm,
                    'hash_code': hash_sha512(f)
                },
                'ocrmypdf': {
                    'pdfa': False
                }
            }

            dm.save()

            if f.content_type == 'application/pdf':
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
