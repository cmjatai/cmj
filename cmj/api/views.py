from django.conf import settings
from django.core.files.base import File
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.utils.translation import ugettext_lazy as _
from django_filters import rest_framework as filters
from rest_framework import viewsets, status, mixins
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated,\
    IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from cmj.api.serializers import DocumentoSerializer,\
    DocumentoUserAnonymousSerializer, DocumentoChoiceSerializer,\
    BiSerializer
from cmj.core.models import Bi
from cmj.sigad.models import Documento, VersaoDeMidia, Midia,\
    ReferenciaEntreDocumentos


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def recria_token(request, pk):
    Token.objects.get(user_id=pk).delete()
    token = Token.objects.create(user_id=pk)

    return Response({"message": "Token recriado com sucesso!", "token": token.key})


class AppVersionView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        content = {
            'name': 'PortalCMJ',
            'description': 'Câmara Municipal de Jataí - Estado de Goiás',
            'version': settings.PORTALCMJ_VERSION,
            'user': request.user.email,
            'is_authenticated': request.user.is_authenticated,
        }
        return Response(content)


class BiViewSet(viewsets.ModelViewSet):
    queryset = Bi.objects.all()
    serializer_class = BiSerializer


class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    permission_classes = (IsAuthenticated,)
    # authentication_classes = (SessionAuthentication, BasicAuthentication)

    #filter_backends = (filters.DjangoFilterBackend,)
    #filter_fields = ('tipo', )

    def list(self, request, *args, **kwargs):
        # FIXME - o método list não deve devolver apenas documentos do tipo
        # banco de imagens. Implementar filtros por tipo
        self.queryset = Documento.objects.qs_bi(
            user=request.user).order_by('-created')

        # DocumentoSerializer é extremamente sobrecarregado, principalmente
        # na devolução de grandes objetos como banco de imagens. Desta forma,
        # e até esta implementação listagem de documentos via REST
        # eram necessários para componentes de seleção como radiobox e checkbox
        # assim foi implementado este desvio de serialização para listagens
        # que não escreve um método completo mas sim um par id, titulo
        self.serializer_class = DocumentoChoiceSerializer
        return viewsets.ModelViewSet.list(self, request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        # FIXME
        if self.request.user.is_anonymous:
            self.serializer_class = DocumentoUserAnonymousSerializer
            self.permission_classes = (IsAuthenticatedOrReadOnly, )
            self.queryset = Documento.objects.qs_docs()

        return viewsets.ModelViewSet.dispatch(self, request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()

        cita = request.data.get('cita', [])

        if cita:
            # FIXME tratar informação cita
            cita = cita[0]
            ref = ReferenciaEntreDocumentos.objects.get(
                pk=cita.pop('id'))
            ref.delete()
            response = Response(status=status.HTTP_204_NO_CONTENT)

        else:
            if obj.tipo in Documento.TDc:
                if obj.parent.childs.count() == 1:
                    raise PermissionDenied(
                        _('Não é permitido remover todos os container'))
            parent, ordem = obj.parent, obj.ordem

            response = viewsets.ModelViewSet.destroy(
                self, request, *args, **kwargs)

            Documento.objects.remove_space(parent, ordem)

        return response

    def perform_destroy(self, instance):
        instance.delete(user=self.request.user)

    def perform_update(self, serializer):
        len_files = len(self.request.FILES)
        instance = serializer.instance
        if not len(self.request.FILES):

            rotate = self.request.data.get('rotate', 0)
            if rotate:
                instance.midia.last.rotate(rotate)

            viewsets.ModelViewSet.perform_update(self, serializer)
            return

        files = self.request.FILES.getlist('files')

        if instance.tipo == Documento.TPD_IMAGE:
            # TPD_IMAGE deve receber apenas um arquivo
            # se por acaso receber mais de um, será ignorado

            if files:
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

        elif instance.tipo == Documento.TPD_FILE:

            if files:
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
                try:
                    with transaction.atomic():
                        ordem += 1

                        image = Documento()
                        image.raiz = instance.raiz
                        image.parent = instance
                        image.visibilidade = Documento.STATUS_RESTRICT
                        image.ordem = ordem
                        image.titulo = ''
                        image.owner = self.request.user
                        image.tipo = Documento.TPD_IMAGE if instance.tipo != \
                            Documento.TPD_CONTAINER_FILE else Documento.TPD_FILE
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

                except:
                    ordem -= 1
