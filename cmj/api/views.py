from django.core.files.base import File
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated,\
    IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from cmj.api.serializers import DocumentoSerializer,\
    DocumentoUserAnonymousSerializer
from cmj.sigad.models import Documento, VersaoDeMidia, Midia


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    permission_classes = (IsAuthenticated,)
    # authentication_classes = (SessionAuthentication, BasicAuthentication)

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_anonymous():
            self.serializer_class = DocumentoUserAnonymousSerializer
            self.permission_classes = (IsAuthenticatedOrReadOnly, )
            self.queryset = Documento.objects.qs_docs()

        return viewsets.ModelViewSet.dispatch(self, request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()

        if obj.tipo in Documento.TDc:
            if obj.parent.childs.count() == 1:
                raise PermissionDenied(
                    _('Não é permitido remover todos os container'))
        parent, ordem = obj.parent, obj.ordem

        response = viewsets.ModelViewSet.destroy(
            self, request, *args, **kwargs)

        Documento.objects.remove_space(parent, ordem)

        return response

    def perform_update(self, serializer):
        if len(self.request.FILES):
            files = self.request.FILES.getlist('files')

            inst = serializer.instance

            if not hasattr(inst, 'midia'):
                midia = Midia()
                midia.documento = serializer.instance
                midia.save()
            else:
                midia = inst.midia

            versao = VersaoDeMidia()
            versao.midia = midia
            versao.owner = self.request.user
            versao.content_type = files[0].content_type
            versao.alinhamento = serializer.instance.alinhamento
            versao.save()

            versao.file.save("image.jpg", File(files[0]), save=True)
        else:
            viewsets.ModelViewSet.perform_update(self, serializer)


class MidiaUpLoadView(APIView):
    parser_classes = (MultiPartParser,)
