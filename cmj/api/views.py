from httplib2 import BasicAuthentication
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated,\
    IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from cmj.api.serializers import DocumentoSerializer,\
    DocumentoUserAnonymousSerializer
from cmj.sigad.models import Documento


class DocumentoViewSet(viewsets.ModelViewSet):
    """
    List e Retrieve
        default = /api/documento/{pk}/?depth_childs=X&depth_citados=Y

            depth_childs = X
            depth_citados = Y
                recupera X e/ou Y profundidade
                em childs e/ou em documentos_citados, respectivamente

                X = 0 e/ou Y = 0 childs e documentos_citados
                tem suas pks listadas
    """
    queryset = Documento.objects.all()
    serializer_class = DocumentoSerializer
    permission_classes = (IsAuthenticated,)
    # authentication_classes = (SessionAuthentication, BasicAuthentication)

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_anonymous():
            self.serializer_class = DocumentoUserAnonymousSerializer
            self.permission_classes = (IsAuthenticatedOrReadOnly, )
            self.queryset = Documento.objects.view_public_docs()

        return viewsets.ModelViewSet.dispatch(self, request, *args, **kwargs)

    @detail_route(methods=['POST'])
    def set_titulo(self, request, pk=None):
        self.object = self.get_object()
        self.object.titulo = request.data.get('titulo', '')
        self.object.save()
        return Response({'message': 'OK'}, status=status.HTTP_206_PARTIAL_CONTENT)

    @detail_route(methods=['POST'])
    def set_descricao(self, request, pk=None):
        self.object = self.get_object()
        self.object.descricao = request.data.get('descricao', '')
        self.object.save()
        return Response({'message': 'OK'}, status=status.HTTP_206_PARTIAL_CONTENT)
