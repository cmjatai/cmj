import logging

from django.apps import apps
from django.conf import settings
from django.utils import formats, timezone

from cmj.celery import app
from cmj.mixins import PluginSignMixin
from sapl.sessao.models import RegistroVotacao
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__) if not settings.DEBUG else logging.getLogger(__name__)


@app.task(queue='cq_core', bind=True)
def task_add_selo_votacao(self,  list_pk):
    logger.info(f'task_add_selo_votacao RegistroVotacao {list_pk}')
    task_add_selo_votacao_function(list_pk)


def task_add_selo_votacao_function(list_pk):
    logger.info(
        f'task_add_selo_votacao_function RegistroVotacao {list_pk}')

    registros_votacao = RegistroVotacao.objects.filter(id__in=list_pk)

    for rv in registros_votacao:
        materia_votada = rv.materia

        votacoes_da_materia = RegistroVotacao.objects.filter(
            materia=materia_votada,
            tipo_resultado_votacao__natureza__in=('A', 'R'),
            ordem__sessao_plenaria__tipo__gera_selo_votacao=True
        ).order_by('data_hora')

        titulopre = ''
        titulo = ''
        titulopos = ''

        v_unica = False

        titulopos_mask = 'Sim: {} - Não: {} - Abstenção: {} - {}'

        # titulopos_mask = f'S: {v.numero_votos_sim} N
        # {v.numero_votos_nao}: A:{v.numero_abstencoes} - {'

        if votacoes_da_materia.count() == 1 and \
                materia_votada.tipo.turnos_aprovacao == 1:
            vot = votacoes_da_materia.first()
            v_unica = True

        count = 1
        for vot in votacoes_da_materia:
            oe = vot.ordem or vot.expediente
            sp = oe.sessao_plenaria

            if sp != rv.ordem.sessao_plenaria:
                count += 1
                continue

            if vot.selo_votacao:
                continue

            titulopre = '{}\n{}'.format(
                sp.str_title(), sp.str_subtitle())
            titulo = str(vot.tipo_resultado_votacao).upper()
            titulopos = titulopos_mask.format(
                vot.numero_votos_sim,
                vot.numero_votos_nao,
                vot.numero_abstencoes,
                '{}{}'.format(
                    'Votação Única' if v_unica else count,
                    '' if v_unica else 'ª Votação'
                )
            )

            paths = materia_votada.texto_original.path

            autor = materia_votada.autores.all().first()
            compression = materia_votada.metadata['selos']['cert_protocolo'].get('compression', False)

            try:
                x = materia_votada.metadata['selos']['cert_protocolo']['x']
                y = materia_votada.metadata['selos']['cert_protocolo']['y'] + \
                    materia_votada.metadata['selos']['cert_protocolo']['h'] + 10
            except:
                x = 190
                y = 120

            psm = PluginSignMixin()

            cmd = psm.cmd_mask

            params = {
                'plugin': psm.plugin_path,
                'comando': 'deliberacao_plenario',
                'in_file': paths,
                'certificado': settings.CERT_PRIVATE_KEY_ID,
                'password': settings.CERT_PRIVATE_KEY_ACCESS,
                'data_ocorrencia': formats.date_format(
                    timezone.localtime(vot.data_hora), 'd/m/Y'
                ),
                'hora_ocorrencia': formats.date_format(
                    timezone.localtime(vot.data_hora), 'H:i'
                ),
                'data_comando': formats.date_format(timezone.localtime(), 'd/m/Y'),
                'hora_comando': formats.date_format(timezone.localtime(), 'H:i'),
                'titulopre': titulopre,
                'titulo': titulo,
                'titulopos': titulopos,
                'x': x,
                'y': (count - 1) * 53 + y,
                'w': 12,
                'h': 50,
                'cor': "0, 76, {}, 255".format(170 - count * 20) if vot.tipo_resultado_votacao.natureza == 'A' else "150, 20, 0, 255",
                'compression': compression,
                'debug': False # settings.DEBUG
            }

            cmd = cmd.format(**params)
            result = psm.run(cmd)

            del params['plugin']
            del params['in_file']
            del params['certificado']
            del params['password']
            del params['debug']
            del params['comando']

            if 'selos' not in materia_votada.metadata:
                materia_votada.metadata['selos'] = {}

            materia_votada.metadata['selos'][f'deliberacao_plenario_{count}'] = params
            materia_votada.save()

            RegistroVotacao.objects.filter(id=vot.id).update(selo_votacao=True)
            # v.selo_votacao = True
            # v.save()
