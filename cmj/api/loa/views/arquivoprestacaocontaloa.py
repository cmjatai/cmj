from rest_framework.decorators import action

from sapl.api.mixins import ResponseFileMixin


class ArquivoPrestacaoContaLoaViewSet(ResponseFileMixin):
    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
