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
        len_files = len(self.request.FILES)
        if not len(self.request.FILES):
            viewsets.ModelViewSet.perform_update(self, serializer)
            return

        instance = serializer.instance
        files = self.request.FILES.getlist('files')

        if instance.tipo == Documento.TPD_IMAGE:
            # TPD_IMAGE deve receber apenas um arquivo
            # se por acaso receber mais de um, será ignorado

            if not hasattr(instance, 'midia'):
                midia = Midia()
                midia.documento = instance
                midia.save()
            else:
                midia = instance.midia

            versao = VersaoDeMidia()
            versao.midia = midia
            versao.owner = self.request.user
            versao.alinhamento = instance.alinhamento
            versao.save(with_file=files[0])

        elif instance.tipo in Documento.TDc:
            ordem = 0
            last_image = instance.childs.view_childs().last()
            if last_image:
                ordem = last_image.ordem

            for file in files:
                ordem += 1
                image = Documento()
                image.raiz = instance.raiz
                image.parent = instance
                image.visibilidade = Documento.STATUS_RESTRICT
                image.ordem = ordem
                image.titulo = ''
                image.owner = self.request.user
                image.tipo = Documento.TPD_IMAGE
                image.classe = instance.classe
                image.save()

                midia = Midia()
                midia.documento = image
                midia.save()

                versao = VersaoDeMidia()
                versao.midia = midia
                versao.owner = self.request.user
                versao.alinhamento = Documento.ALINHAMENTO_JUSTIFY
                versao.save(with_file=file)
