
from django.apps.registry import apps
from django.db.models import Q
from django.utils.text import slugify
from rest_framework.decorators import action
from rest_framework.response import Response

from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl.api.mixins import ResponseFileMixin
from sapl.api.permissions import SaplModelPermissions
from sapl.materia.models import TipoMateriaLegislativa, Tramitacao,\
    MateriaLegislativa, Proposicao, TipoProposicao, DocumentoAcessorio


ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('materia')
    ]
)


@customize(TipoProposicao)
class _TipoProposicaoViewset:

    @action(detail=False, methods=['GET'])
    def tipos_do_autor_contectado(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs = qs.filter(
            tipo_autores=request.user.autor_set.first().tipo)

        if qs.exists() and qs[0].tipo_conteudo_related._meta.model == TipoMateriaLegislativa:
            qs = qs.order_by(
                'tipomaterialegislativa_set__sequencia_regimental')
        self.queryset = qs
        return self.list(request, *args, **kwargs)


@customize(Proposicao)
class _ProposicaoViewSet(ResponseFileMixin):
    """
    list:
        Retorna lista de Proposições

        * Permissões:

            * Usuário Dono:
                * Pode listar todas suas Proposições

            * Usuário Conectado ou Anônimo:
                * Pode listar todas as Proposições incorporadas

    retrieve:
        Retorna uma proposição passada pelo 'id'

        * Permissões:

            * Usuário Dono:
                * Pode recuperar qualquer de suas Proposições

            * Usuário Conectado ou Anônimo:
                * Pode recuperar qualquer das proposições incorporadas

    """
    class ProposicaoPermission(SaplModelPermissions):
        def has_permission(self, request, view):
            if request.method == 'GET':
                return True
                # se a solicitação é list ou detail, libera o teste de permissão
                # e deixa o get_queryset filtrar de acordo com a regra de
                # visibilidade das proposições, ou seja:
                # 1. proposição incorporada é proposição pública
                # 2. não incorporada só o autor pode ver
            else:
                perm = super().has_permission(request, view)
                return perm
                # não é list ou detail, então passa pelas regras de permissão e,
                # depois disso ainda passa pelo filtro de get_queryset

    permission_classes = (ProposicaoPermission, )

    def get_queryset(self):
        qs = super().get_queryset()

        # se usuário anônimo, pode ver apenas proposições recebidas
        q = Q(data_recebimento__isnull=False, object_id__isnull=False)
        if not self.request.user.is_anonymous:

            autor_do_usuario_logado = self.request.user.autor_set.first()

            # se usuário logado é operador de algum autor
            if autor_do_usuario_logado:
                q = Q(autor=autor_do_usuario_logado)

            # se é operador de protocolo, ve qualquer coisa enviada
            if self.request.user.has_perm('protocoloadm.list_protocolo'):
                q = Q(data_envio__isnull=False) | Q(
                    data_devolucao__isnull=False)

        qs = qs.filter(q)
        return qs

    @action(detail=True)
    def texto_original(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)


@customize(MateriaLegislativa)
class _MateriaLegislativaViewSet(ResponseFileMixin):

    def custom_filename(self, item):
        arcname = '{}-{:03d}-{}-{}.{}'.format(
            item.ano,
            item.numero,
            slugify(item.tipo.sigla),
            slugify(item.tipo.descricao),
            item.texto_original.path.split('.')[-1])
        return arcname

    @action(detail=True)
    def texto_original(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)

    @action(detail=True, methods=['GET'])
    def ultima_tramitacao(self, request, *args, **kwargs):

        materia = self.get_object()
        if not materia.tramitacao_set.exists():
            return Response({})

        ultima_tramitacao = materia.tramitacao_set.first()

        serializer_class = ApiViewSetConstrutor.get_viewset_for_model(
            Tramitacao).serializer_class(ultima_tramitacao)

        return Response(serializer_class.data)

    @action(detail=True, methods=['GET'])
    def anexadas(self, request, *args, **kwargs):
        self.queryset = self.get_object().anexadas.materias_anexadas()
        return self.list(request, *args, **kwargs)

    @action(detail=True, methods=['GET'])
    def desanexadas(self, request, *args, **kwargs):
        self.queryset = self.get_object().anexadas.materias_desanexadas()
        return self.list(request, *args, **kwargs)


@customize(TipoMateriaLegislativa)
class _TipoMateriaLegislativaViewSet:

    @action(detail=True, methods=['POST'])
    def change_position(self, request, *args, **kwargs):
        result = {
            'status': 200,
            'message': 'OK'
        }
        d = request.data
        if 'pos_ini' in d and 'pos_fim' in d:
            if d['pos_ini'] != d['pos_fim']:
                pk = kwargs['pk']
                TipoMateriaLegislativa.objects.reposicione(pk, d['pos_fim'])

        return Response(result)


@customize(DocumentoAcessorio)
class _DocumentoAcessorioViewSet(ResponseFileMixin):

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
