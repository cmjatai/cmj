
from functools import partial
from django.apps.registry import apps
from rest_framework.decorators import action
from rest_framework.response import Response

from cmj.utils import get_client_ip
from django.db.models import Q
from drfautoapi.drfautoapi import ApiViewSetConstrutor, \
    customize, wrapper_queryset_response_for_drf_action
from sapl import materia, sessao
from sapl.api.mixins import ResponseFileMixin
from sapl.api.serializers import ChoiceSerializer,\
    SessaoPlenariaECidadaniaSerializer
from sapl.sessao.models import ExpedienteMateria, IntegranteMesa, PresencaOrdemDia, RegistroLeitura, RegistroVotacao, SessaoPlenaria, ExpedienteSessao, OrdemDia, SessaoPlenariaPresenca, TipoResultadoVotacao, VotoParlamentar
from sapl.utils import choice_anos_com_sessaoplenaria


ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('sessao')
    ]
)


@customize(SessaoPlenaria)
class _SessaoPlenariaViewSet(ResponseFileMixin):

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @action(detail=False)
    def years(self, request, *args, **kwargs):
        years = choice_anos_com_sessaoplenaria()

        serializer = ChoiceSerializer(years, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def expedientes(self, request, *args, **kwargs):
        return self.get_expedientes()

    @wrapper_queryset_response_for_drf_action(model=ExpedienteSessao)
    def get_expedientes(self):
        return self.get_queryset().filter(sessao_plenaria_id=self.kwargs['pk'])

    @action(detail=True)
    def upload_ata(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)

    @action(detail=True)
    def upload_pauta(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)

    @action(detail=True)
    def upload_anexo(self, request, *args, **kwargs):
        return self.response_file(request, *args, **kwargs)

    @action(detail=True)
    def ecidadania(self, request, *args, **kwargs):
        self.serializer_class = SessaoPlenariaECidadaniaSerializer
        return self.retrieve(request, *args, **kwargs)

    @action(detail=False, url_path='ecidadania')
    def ecidadania_list(self, request, *args, **kwargs):
        self.serializer_class = SessaoPlenariaECidadaniaSerializer
        return self.list(request, *args, **kwargs)

@customize(VotoParlamentar)
class _VotoParlamentarViewSet:

    def perform_create(self, serializer):
        serializer.save(ip=get_client_ip(self.request), user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(ip=get_client_ip(self.request), user=self.request.user)
    #def get_serializer(self, *args, **kwargs):
    #    if hasattr(self.request, '_request') and self.request._request.method in ['POST', 'PUT', 'PATCH']:
    #        data = kwargs.get('data', None)
    #        data['ip'] = get_client_ip(self.request)
    #        kwargs['data'] = data
    #    return super().get_serializer(*args, **kwargs)

class ChangeExpMatOrdemDiaMixin:

    def toggle_action(self, action_name):
        item = self.get_object()

        old_value = getattr(item, action_name)

        item.discussao_aberta = False
        item.votacao_aberta = False
        item.votacao_aberta_pedido_prazo = False
        item.registro_aberto = False

        setattr(item, action_name, not old_value)

        if item.votacao_aberta_pedido_prazo:
            item.votacao_aberta = True
            item.registro_aberto = True

        if getattr(item, action_name):
            q = Q(
                sessao_plenaria=item.sessao_plenaria
            ) & (
                    Q(
                        discussao_aberta=True
                    ) | Q(
                            votacao_aberta=True
                    ) | Q(
                            votacao_aberta_pedido_prazo=True
                    )
                )

            models = [OrdemDia, ExpedienteMateria]

            for m in models:

                qs = m.objects.filter(q)
                if m._meta.model == item._meta.model:
                    qs = qs.exclude(id=item.id)

                for obj in qs:
                    obj.discussao_aberta = False
                    obj.votacao_aberta = False
                    obj.votacao_aberta_pedido_prazo = False
                    obj.registro_aberto = False
                    obj.save()


        item.save()
        serializer = self.get_serializer(item)

        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def toggle_state(self, request, *args, **kwargs):
        field = request.data.get('field', None)
        if field not in ['discussao_aberta', 'votacao_aberta', 'votacao_aberta_pedido_prazo']:
            return Response({'detail': 'Field inválido.'}, status=400)
        return self.toggle_action(field)

    @action(detail=True, methods=['patch'])
    def action_cancelar_registrovotacao(self, request, *args, **kwargs):
        item = self.get_object()
        item.resultado = ''
        item.discussao_aberta = False
        item.votacao_aberta = False
        item.votacao_aberta_pedido_prazo = False
        item.registro_aberto = False

        # exclui todas as votações parlamentares sem registro de votação
        v = None
        for v in VotoParlamentar.objects.filter(
            expediente=item if item._meta.model == ExpedienteMateria else None,
            ordem=item if item._meta.model == OrdemDia else None,
            votacao=None
            ):
            v.delete()

        if v:
            item.save()
            return Response({'detail': 'Votações parlamentares sem registro de votação excluídas.'})

        registros = list(item.registrovotacao_set.order_by('-id'))

        if registros:
            item.resultado = '' if len(registros) == 1 else registros[1].tipo_resultado_votacao.nome
            registro = registros[0]
            registro.delete()
        item.save()
        return Response({'detail': 'Registro de votação cancelado com sucesso.'})

    @action(detail=True, methods=['patch'])
    def action_registrovotacao(self, request, *args, **kwargs):
        item = self.get_object()
        unanime = request.data.get('unanime', False)

        if unanime:
            return self.action_registrovotacao_unanime(request, *args, **kwargs)

        form = request.data

        tipo_resultado_votacao_id = form.get('tipo_resultado_votacao', None)
        if not tipo_resultado_votacao_id:
            return Response({'detail': 'Tipo de resultado de votação é obrigatório.'}, status=400)

        votos = VotoParlamentar.objects.filter(
            expediente=item if item._meta.model == ExpedienteMateria else None,
            ordem=item if item._meta.model == OrdemDia else None,
            votacao=None
            )

        registro = RegistroVotacao()
        registro.materia = item.materia
        registro.expediente = item if item._meta.model == ExpedienteMateria else None
        registro.ordem = item if item._meta.model == OrdemDia else None
        registro.numero_votos_sim = votos.filter(voto='Sim').count()
        registro.numero_votos_nao = votos.filter(voto='Não').count()
        registro.numero_abstencoes = votos.filter(voto='Abstenção').count()
        registro.observacao = form.get('observacao', '')

        registro.user = request.user
        registro.ip = get_client_ip(request)


        registro.tipo_resultado_votacao_id = tipo_resultado_votacao_id
        registro.save()

        for v in votos:
            v.votacao = registro
            v.save()

        item.votacao_aberta = False
        item.votacao_aberta_pedido_prazo = False
        item.discussao_aberta = False
        item.registro_aberto = False
        item.resultado = registro.tipo_resultado_votacao.nome
        item.save()

        return Response({'detail': 'Registro de votação efetuado com sucesso.'})

    def action_registrovotacao_unanime(self, request, *args, **kwargs):
        resultado_unanime = request.data.get('resultado', None)

        if resultado_unanime not in ['A', 'R', None]:
            return Response({'detail': 'Resultado inválido.'}, status=400)

        com_presidente = request.data.get('com_presidente', False)

        item = self.get_object()

        #if not item.votacao_aberta and not item.votacao_aberta_pedido_prazo:
        #    return Response({
        #        'detail': 'Votação não está aberta.',
        #        'type': 'danger'
        #        }, status=400)

        # presentes na sessao
        sessao = item.sessao_plenaria
        model_presentes = PresencaOrdemDia if item._meta.model == OrdemDia else SessaoPlenariaPresenca
        count_presentes = model_presentes.objects.filter(sessao_plenaria=sessao).count()

        presidente_da_sessao = IntegranteMesa.objects.filter(
            sessao_plenaria=sessao,
            cargo__presidente=True
        ).first()
        presidente_da_sessao = presidente_da_sessao.parlamentar if presidente_da_sessao else None

        if not com_presidente:
            count_presentes -= 1

        naturezas_esperadas = {
            'A': 'Aprovado Unânime',
            'R': 'Rejeitado Unânime',
            'P': 'Pedido de Adiamento'
        }

        if not item.votacao_aberta_pedido_prazo:
            naturezas_esperadas.pop('P')
        else:
            item.registrovotacao_set.all().delete()

        registro = item.registrovotacao_set.filter(
          tipo_resultado_votacao__natureza__in=list(naturezas_esperadas.keys())
        ).first()

        if registro:
            for v in VotoParlamentar.objects.filter(
                votacao=registro):
                v.delete()
            registro.delete()
        else:
            # exclui todas as votações parlamentares sem registro de votação
            for v in VotoParlamentar.objects.filter(
                expediente=item if item._meta.model == ExpedienteMateria else None,
                ordem=item if item._meta.model == OrdemDia else None
                ):
                v.delete()

        registro = RegistroVotacao()
        registro.materia = item.materia
        registro.expediente = item if item._meta.model == ExpedienteMateria else None
        registro.ordem = item if item._meta.model == OrdemDia else None
        registro.numero_votos_sim = count_presentes if resultado_unanime == 'A' else 0
        registro.numero_votos_nao = count_presentes if resultado_unanime == 'R' else 0
        registro.numero_abstencoes = 0

        registro.user = request.user
        registro.ip = get_client_ip(request)

        # TODO: refatorar tiporesultadovotacao
        if not item.votacao_aberta_pedido_prazo:
            registro.tipo_resultado_votacao = TipoResultadoVotacao.objects.get(
                natureza=resultado_unanime,
                nome='Aprovado' if resultado_unanime == 'A' else 'Rejeitado'
                )
        else:
            registro.tipo_resultado_votacao = TipoResultadoVotacao.objects.get(
                natureza='P',
                nome='Prazo Regimental'
                )

        registro.save()

        item.votacao_aberta = False
        item.votacao_aberta_pedido_prazo = False
        item.discussao_aberta = False
        item.resultado = registro.tipo_resultado_votacao.nome
        item.save()

        for p in model_presentes.objects.filter(sessao_plenaria=sessao):

            if not com_presidente and p.parlamentar == presidente_da_sessao:
                continue

            voto = VotoParlamentar()
            voto.votacao = registro
            voto.parlamentar = p.parlamentar
            voto.expediente = item if item._meta.model == ExpedienteMateria else None
            voto.ordem = item if item._meta.model == OrdemDia else None
            voto.materia = item.materia

            if resultado_unanime == 'A':
                voto.voto = 'Sim'
            elif resultado_unanime == 'R':
                voto.voto = 'Não'

            voto.user = request.user
            voto.ip = get_client_ip(request)

            voto.save()

        return Response({'detail': 'Registro de votação criado com sucesso.'})

    @action(detail=True, methods=['patch'])
    def action_cancelar_registroleitura(self, request, *args, **kwargs):
        item = self.get_object()

        registros = list(item.registroleitura_set.order_by('-id'))

        if registros:
            item.resultado = '' if len(registros) == 1 else registros[1].tipo_resultado_votacao.nome
            item.save()
            registro = registros[0]
            registro.delete()
        else:
            return Response({'detail': 'Nenhum registro de leitura encontrado.'}, status=400)

        return Response({'detail': 'Registro de leitura cancelado com sucesso.'})

    @action(detail=True, methods=['patch'])
    def action_registroleitura(self, request, *args, **kwargs):

        item = self.get_object()
        # presentes na sessao
        sessao = item.sessao_plenaria

        registro = item.registroleitura_set.all().first()

        if registro:
            registro.delete()

        registro = RegistroLeitura()
        registro.materia = item.materia
        registro.expediente = item if item._meta.model == ExpedienteMateria else None
        registro.ordem = item if item._meta.model == OrdemDia else None

        registro.user = request.user
        registro.ip = get_client_ip(request)

        registro.save()

        item.votacao_aberta = False
        item.votacao_aberta_pedido_prazo = False
        item.discussao_aberta = False
        item.resultado = 'Materia Lida'
        item.save()

        return Response({'detail': 'Registro de leitura criado com sucesso.'})







@customize(OrdemDia)
class _OrdemDiaViewSet(ChangeExpMatOrdemDiaMixin):
    pass


@customize(ExpedienteMateria)
class _ExpedienteMateriaViewSet(ChangeExpMatOrdemDiaMixin):
    pass

@customize(RegistroVotacao)
class _RegistroVotacaoViewSet:

    def perform_create(self, serializer):
        serializer.save(ip=get_client_ip(self.request))