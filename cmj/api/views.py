from httplib2 import BasicAuthentication
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated,\
    IsAuthenticatedOrReadOnly

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
