from django.conf import settings
from django.contrib.auth import login, logout
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from image_cropping.utils import get_backend
from rest_framework import viewsets, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated,\
    IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from webpack_loader.utils import get_static

from cmj.api.serializers import DocumentoSerializer,\
    DocumentoUserAnonymousSerializer, DocumentoChoiceSerializer
from cmj.core.models import Bi
from cmj.sigad.models import Documento, VersaoDeMidia, Midia,\
    ReferenciaEntreDocumentos
from drfautoapi.drfautoapi import ApiViewSetConstrutor
from sapl.api.views import LastModifiedDecorator


class AppVersionView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):

        content = {
            'name': 'PortalCMJ',
            'description': 'PortalCMJ',
            'version': settings.PORTALCMJ_VERSION,
        }

        if request.user.is_authenticated:
            #token = Token.objects.filter(user=request.user).first()
            #    'token': token.key,
            content['is_authenticated'] = True
            content['permissions'] = sorted(request.user.get_all_permissions())

            try:
                avatar = get_static('img/perfil.jpg') if not request.user.avatar else \
                get_backend().get_thumbnail_url(
                    request.user.avatar,
                    {
                        'size': (128, 128),
                        'box': request.user.cropping,
                        'crop': True,
                        'detail': True,
                    })
            except:
                avatar = get_static('img/perfil.jpg')

            user = {
                'id': request.user.id,
                'username': request.user.username,
                'fullname': request.user.get_full_name(),

                'avatar': avatar

            }
            votante = request.user.votante.first()
            if votante:
                user.update({
                    'votante': {
                        'parlamentar_id': votante.parlamentar_id,
                        'nome_parlamentar': votante.parlamentar.nome_parlamentar
                    }
                })
            content.update({
                'user': user
            })

        return Response(content)


class AppSessionAuthView(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({'detail': _('Autenticação efetuada com sucesso!')})

    def delete(self, request):
        logout(request)
        return Response({'detail': _('Desconexão efetuada com sucesso!')})

    def options(self, request, *args, **kwargs):
        perm = request.GET.get('perm', None)
        if perm:
            if not request.user.has_perm(perm):
                return Response({'status': 'fail', 'detail': _('Usuário não possui permissão: %s') % perm})
            return Response({'status': 'ok', 'detail': _('Usuário possui permissão: %s') % perm})
        return super().options(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return Response({
                'permissions': sorted(request.user.get_all_permissions()),
                'detail': _('Usuário autenticado'),
            })
        return super().options(request, *args, **kwargs)


CmjApiViewSetConstrutor = ApiViewSetConstrutor
CmjApiViewSetConstrutor.last_modified_class(LastModifiedDecorator)
CmjApiViewSetConstrutor.import_modules([
    'cmj.api.views_core',
    'cmj.api.views_agenda',
    'cmj.api.views_videos',
    'cmj.api.views_arq',
    'cmj.api.views_cerimonial',
    'cmj.api.views_diarios',
    'cmj.api.views_loa',
    'cmj.api.views_painelset',
]
)

# class BiViewSet(viewsets.ModelViewSet):
#    queryset = Bi.objects.all()
#    serializer_class = BiSerializer


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
