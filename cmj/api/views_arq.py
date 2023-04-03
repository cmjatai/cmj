from datetime import datetime
import logging
from operator import attrgetter

from django.apps.registry import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.aggregates import Max
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

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
                }
            }
            dm.save()

        serializer = self.get_serializer(draft)
        return Response(serializer.data)


@customize(DraftMidia)
class _DraftMidia(ResponseFileMixin):

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
