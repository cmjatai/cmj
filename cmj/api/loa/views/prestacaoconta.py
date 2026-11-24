from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from cmj.loa.services.s_prestacaoconta import PrestacaoContaService


class FiltrosDaPrestacaoConta(serializers.Serializer):
    """Formato dos parâmetros das consultas (LOA-PCC-001 a 004). As regras ficam
    no serviço."""

    TIPOS = (0, 10, 99)
    PAGE_SIZE_MAXIMO = 100

    situacao = serializers.CharField(required=False, max_length=100)
    search = serializers.CharField(required=False, max_length=200)
    unidade = serializers.IntegerField(required=False, min_value=1)
    entidade = serializers.IntegerField(required=False, min_value=1)
    parlamentar = serializers.IntegerField(required=False, min_value=1)
    tipo__in = serializers.CharField(required=False, max_length=50)
    ajustes = serializers.BooleanField(required=False, default=False)
    loas = serializers.CharField(required=False, max_length=200)
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, default=10)

    @staticmethod
    def _inteiros(value):
        try:
            return [int(parte) for parte in value.split(",") if parte.strip()]
        except ValueError:
            raise serializers.ValidationError("Informe números separados por vírgula.")

    def validate_tipo__in(self, value):
        tipos = self._inteiros(value)
        if any(tipo not in self.TIPOS for tipo in tipos):
            raise serializers.ValidationError("Tipo inexistente.")
        return tipos

    def validate_loas(self, value):
        return self._inteiros(value)

    def validate_page_size(self, value):
        return min(value, self.PAGE_SIZE_MAXIMO)


class PrestacaoContaActions:
    """Consulta consolidada da prestação de contas
    (docs/specs/loa/prestacao-contas-consulta.md). Só validam a entrada e
    chamam o serviço."""

    prestacao_conta = PrestacaoContaService()

    def _consultar_prestacao_conta(self, request, consulta, paginada=False):
        # sem os filtros da rota de LOA: os parâmetros são da consulta
        loa = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        self.check_object_permissions(request, loa)

        campos = FiltrosDaPrestacaoConta().fields
        entrada = {
            nome: request.query_params[nome]
            for nome in campos
            if request.query_params.get(nome, "") != ""
        }
        filtros = FiltrosDaPrestacaoConta(data=entrada)
        filtros.is_valid(raise_exception=True)
        dados = dict(filtros.validated_data)
        dados["tipos"] = dados.pop("tipo__in", [])
        page, page_size = dados.pop("page"), dados.pop("page_size")

        servico = self.prestacao_conta
        try:
            if paginada:
                return Response(
                    servico.itens(request.user, loa, dados, page, page_size)
                )
            return Response(getattr(servico, consulta)(request.user, loa, dados))
        except servico.LoaIndisponivel:
            raise NotFound()
        except servico.PaginaInexistente:
            raise NotFound("Página inexistente.")
        except servico.FiltroInvalido as e:
            raise ValidationError(e.erros)

    @action(detail=True, methods=["get"])
    def prestacaoconta_resumo(self, request, *args, **kwargs):
        return self._consultar_prestacao_conta(request, "resumo")

    @action(detail=True, methods=["get"])
    def prestacaoconta_dashboard(self, request, *args, **kwargs):
        return self._consultar_prestacao_conta(request, "dashboard")

    @action(detail=True, methods=["get"])
    def prestacaoconta_opcoes(self, request, *args, **kwargs):
        return self._consultar_prestacao_conta(request, "opcoes")

    @action(detail=True, methods=["get"])
    def prestacaoconta_itens(self, request, *args, **kwargs):
        return self._consultar_prestacao_conta(request, "itens", paginada=True)
