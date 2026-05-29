from django.apps.registry import apps
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_409_CONFLICT,
)

from drfautoapi.drfautoapi import (
    ApiViewSetConstrutor,
    customize,
)
from sapl.api.mixins import ResponseFileMixin
from sapl.api.permissions import SaplModelPermissions
from sapl.materia.models import (
    DocumentoAcessorio,
    MateriaLegislativa,
    Proposicao,
    ProposicaoAssinante,
    TipoMateriaLegislativa,
    TipoProposicao,
    Tramitacao,
)

ApiViewSetConstrutor.build_class([apps.get_app_config("materia")])


@customize(TipoProposicao)
class _TipoProposicaoViewset:

    @action(detail=False, methods=["GET"])
    def tipos_do_autor_contectado(self, request, *args, **kwargs):
        qs = self.get_queryset()
        qs = qs.filter(tipo_autores=request.user.autor_set.first().tipo)

        if (
            qs.exists()
            and qs[0].tipo_conteudo_related._meta.model == TipoMateriaLegislativa
        ):
            qs = qs.order_by("tipomaterialegislativa_set__sequencia_regimental")
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
            if request.method == "GET":
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

    permission_classes = (ProposicaoPermission,)

    def get_queryset(self):
        qs = super().get_queryset()

        # se usuário anônimo, pode ver apenas proposições recebidas
        q = Q(data_recebimento__isnull=False, object_id__isnull=False)
        if not self.request.user.is_anonymous:

            autor_do_usuario_logado = self.request.user.autor_set.first()

            # se usuário logado é operador de algum autor
            if autor_do_usuario_logado:
                q = Q(autor=autor_do_usuario_logado)
            else:
                q = Q()

            # se é operador de protocolo, ve qualquer coisa enviada
            if self.request.user.has_perm("protocoloadm.list_protocolo"):
                q |= Q(data_envio__isnull=False) | Q(data_devolucao__isnull=False)

        qs = qs.filter(q)
        return qs

    def custom_filename(self, item):
        arcname = "{}-{}-{:03d}-proposicao-{}.{}".format(
            item.ano,
            slugify(item.autor),
            item.numero_proposicao,
            slugify(item.tipo),
            item.texto_original.path.split(".")[-1],
        )
        return arcname

    @action(detail=True)
    def texto_original(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    def assinantes(self, request, *args, **kwargs):
        proposicao = self.get_object()
        qs = (
            ProposicaoAssinante.objects.filter(proposicao=proposicao)
            .select_related("autor")
            .order_by("autor__nome")
        )
        data = [
            {
                "autor_id": pa.autor_id,
                "autor": str(pa.autor),
                "status": pa.status,
                "status_display": pa.get_status_display(),
                "data_captura": pa.data_captura,
                "data_assinatura": pa.data_assinatura,
            }
            for pa in qs
        ]
        return Response(data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def capturar_assinatura(self, request, *args, **kwargs):
        from datetime import timedelta

        proposicao = self.get_object()

        if proposicao.data_envio is not None:
            return Response(
                {
                    "detail": "Esta proposição já foi enviada e não aceita mais assinaturas."
                },
                status=HTTP_400_BAD_REQUEST,
            )

        autor = request.user.autor_set.first()
        if not autor:
            return Response(
                {"detail": "Usuário não possui Autor vinculado."},
                status=HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            assinantes = list(
                ProposicaoAssinante.objects.select_for_update()
                .filter(proposicao=proposicao)
                .select_related("autor")
            )

            # Auto-liberar locks expirados (mais de 5 minutos)
            expiracao = timezone.now() - timedelta(minutes=5)
            for pa in assinantes:
                if (
                    pa.status == ProposicaoAssinante.STATUS_EM_ASSINATURA
                    and pa.data_captura
                    and pa.data_captura < expiracao
                ):
                    pa.status = ProposicaoAssinante.STATUS_PENDENTE
                    pa.data_captura = None
                    pa.save(update_fields=["status", "data_captura"])

            meu_registro = next(
                (pa for pa in assinantes if pa.autor_id == autor.pk), None
            )
            if not meu_registro:
                return Response(
                    {"detail": "Você não é um assinante desta proposição."},
                    status=HTTP_403_FORBIDDEN,
                )

            if meu_registro.status == ProposicaoAssinante.STATUS_ASSINADO:
                return Response(
                    {"detail": "Você já assinou esta proposição."},
                    status=HTTP_400_BAD_REQUEST,
                )

            if meu_registro.status == ProposicaoAssinante.STATUS_EM_ASSINATURA:
                return Response(
                    {
                        "detail": "Você já possui uma captura de assinatura ativa para esta proposição."
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

            em_assinatura = next(
                (
                    pa
                    for pa in assinantes
                    if pa.status == ProposicaoAssinante.STATUS_EM_ASSINATURA
                ),
                None,
            )
            if em_assinatura:
                return Response(
                    {
                        "detail": f"O Autor {em_assinatura.autor} está assinando no momento."
                    },
                    status=HTTP_409_CONFLICT,
                )

            meu_registro.status = ProposicaoAssinante.STATUS_EM_ASSINATURA
            meu_registro.data_captura = timezone.now()
            meu_registro.save(update_fields=["status", "data_captura"])

        return Response(
            {
                "detail": "Assinatura capturada com sucesso.",
                "hash_code": proposicao.hash_code,
                "data_captura": meu_registro.data_captura,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def liberar_assinatura(self, request, *args, **kwargs):
        proposicao = self.get_object()
        autor = request.user.autor_set.first()

        if not autor:
            return Response(
                {"detail": "Usuário não possui Autor vinculado."},
                status=HTTP_403_FORBIDDEN,
            )

        try:
            pa = ProposicaoAssinante.objects.get(
                proposicao=proposicao,
                autor=autor,
                status=ProposicaoAssinante.STATUS_EM_ASSINATURA,
            )
        except ProposicaoAssinante.DoesNotExist:
            return Response(
                {
                    "detail": "Nenhuma captura de assinatura ativa encontrada para este autor."
                },
                status=HTTP_400_BAD_REQUEST,
            )

        pa.status = ProposicaoAssinante.STATUS_PENDENTE
        pa.data_captura = None
        pa.save(update_fields=["status", "data_captura"])

        return Response({"detail": "Assinatura liberada com sucesso."})

    def perform_update(self, serializer):
        inst = serializer.instance
        # Validar lock ativo quando o arquivo assinado é enviado por um assinante
        if (
            "texto_original" in serializer.validated_data
            and not self.request.user.is_anonymous
        ):
            autor = self.request.user.autor_set.first()
            if autor:
                is_signer = inst.assinantes.filter(autor=autor).exists()
                if is_signer:
                    has_lock = inst.assinantes.filter(
                        autor=autor,
                        status=ProposicaoAssinante.STATUS_EM_ASSINATURA,
                    ).exists()
                    if not has_lock:
                        raise PermissionDenied(
                            "Você precisa capturar a assinatura antes de enviar o arquivo assinado."
                        )
        inst = serializer.save()
        inst.save()


@customize(MateriaLegislativa)
class _MateriaLegislativaViewSet(ResponseFileMixin):

    def custom_filename(self, item):
        arcname = "{}-{:03d}-{}-{}.{}".format(
            item.ano,
            item.numero,
            slugify(item.tipo.sigla),
            slugify(item.tipo.descricao),
            item.texto_original.path.split(".")[-1],
        )
        return arcname

    @action(detail=True)
    def texto_original(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)

    @staticmethod
    def _existe_materia(tipo, numero, ano):
        """Verifica unicidade (tipo, numero, ano) via código."""
        return MateriaLegislativa.objects.filter(
            tipo_id=tipo, numero=numero, ano=ano
        ).exists()

    def create(self, request, *args, **kwargs):
        data = dict(request.data)
        tipo = data.get("tipo", None)
        numero = data.get("numero", None)
        ano = data.get("ano", None)

        if tipo and not numero:
            # Número não fornecido pelo cliente: auto-gerar próximo disponível.
            # select_for_update() em get_proximo_numero previne race conditions.
            with transaction.atomic():
                numero_gerado, ano_gerado = MateriaLegislativa.get_proximo_numero(
                    tipo=tipo, ano=ano
                )
                data["numero"] = numero_gerado
                data["ano"] = ano_gerado

                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(
                    serializer.data, status=HTTP_201_CREATED, headers=headers
                )

        # Número fornecido pelo cliente (ou tipo ausente):
        # validar unicidade (tipo, numero, ano) via código antes de criar.
        if tipo and numero and ano:
            if self._existe_materia(tipo, numero, ano):
                return Response(
                    {
                        "numero": [
                            "O número %s já está em uso para este tipo/ano. "
                            'Remova o campo "numero" para auto-gerar o próximo disponível.'
                            % numero
                        ]
                    },
                    status=HTTP_409_CONFLICT,
                )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["GET"])
    def ultima_tramitacao(self, request, *args, **kwargs):

        materia = self.get_object()
        if not materia.tramitacao_set.exists():
            return Response({})

        ultima_tramitacao = materia.tramitacao_set.first()

        serializer_class = ApiViewSetConstrutor.get_viewset_for_model(
            Tramitacao
        ).serializer_class(ultima_tramitacao)

        return Response(serializer_class.data)

    @action(detail=True, methods=["GET"])
    def anexadas(self, request, *args, **kwargs):
        self.queryset = self.get_object().anexadas.materias_anexadas()
        return self.list(request, *args, **kwargs)

    @action(detail=True, methods=["GET"])
    def desanexadas(self, request, *args, **kwargs):
        self.queryset = self.get_object().anexadas.materias_desanexadas()
        return self.list(request, *args, **kwargs)

    def last_modified_func(self, request, *args, **kwargs):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(request, self.queryset, self)

        timestamp = (
            queryset.order_by("-data_ultima_atualizacao")
            .values_list("data_ultima_atualizacao", flat=True)[:1]
            .first()
        )
        return timestamp


@customize(TipoMateriaLegislativa)
class _TipoMateriaLegislativaViewSet:

    @action(detail=True, methods=["POST"])
    def change_position(self, request, *args, **kwargs):
        result = {"status": 200, "message": "OK"}
        d = request.data
        if "pos_ini" in d and "pos_fim" in d:
            if d["pos_ini"] != d["pos_fim"]:
                pk = kwargs["pk"]
                TipoMateriaLegislativa.objects.reposicione(pk, d["pos_fim"])

        return Response(result)


@customize(DocumentoAcessorio)
class _DocumentoAcessorioViewSet(ResponseFileMixin):

    @action(detail=True)
    def arquivo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)
