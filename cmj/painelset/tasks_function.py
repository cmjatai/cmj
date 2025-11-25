
#logger = logging.getLogger(__name__)
from celery.utils.log import get_task_logger
from django.apps import apps
from django.db.models import Q, F

from cmj.painelset.models import Evento, Painel, VisaoDePainel
from sapl import sessao
from sapl.sessao.models import SessaoPlenaria

logger = get_task_logger(__name__)

def task_refresh_states_from_visaodepainel_function(*args, **kwargs):
    """avaliar visao de painel com base nas chains do campo config de cada visao de painel"""
    # todos os eventos não finalizados

    visoes_changed = {
        'deactivated': [],
        'activated': []
    }

    eventos = {}

    for v in VisaoDePainel.objects.filter(
        painel__evento__end_real__isnull=True,
        painel__auto_select_visoes=True
    ).annotate(
        evento_id=F('painel__evento_id'),
        sessao_id=F('painel__sessao_id'),
    ).order_by(
        'painel__evento_id', 'painel__id', 'position'
    ):
        painel_id = v.painel_id
        evento_id = v.evento_id

        if evento_id not in eventos:
            eventos[evento_id] = {painel_id: []}
        elif painel_id not in eventos[evento_id]:
            eventos[evento_id][painel_id] = []

        eventos[evento_id][painel_id].append(v)

    for evento_id, paineis in eventos.items():
        for painel_id, visoes in paineis.items():

            visao_ja_ativada = False

            for visao in visoes:
                if visao_ja_ativada:
                    visoes_changed['deactivated'].append(visao)
                    continue

                #print( '------------------------------------------------')
                #print(visao.name)

                activates = visao.config.get('activates', []) or []

                for activate in activates:
                    filter_match = []
                    for key, lookups in activate.items():
                        #print(key, lookups)
                        if key != 'activate' or not lookups:
                            continue
                        try:
                            for key_lookup, condition in lookups.items():
                                filter_maps = {}
                                app_label, model_name, field_name = key_lookup.split('__', 2)
                                filter_maps.setdefault((app_label, model_name), {})[field_name] = condition['value']

                                for (app_label, model_name), filter_fields in filter_maps.items():
                                    Model = apps.get_model(app_label, model_name)
                                    fields_relations = dict([
                                        (field.name, field.related_model)
                                        for field in Model._meta.get_fields()
                                        if field.is_relation and hasattr(field, 'related_model')
                                    ])
                                    for field_name, related_model in fields_relations.items():
                                        if related_model == Evento:
                                            filter_fields[f'{field_name}'] = evento_id
                                        elif related_model == Painel:
                                            filter_fields[f'{field_name}'] = painel_id
                                        elif related_model == VisaoDePainel:
                                            filter_fields[f'{field_name}'] = visao.id
                                        elif visao.sessao_id and related_model == SessaoPlenaria:
                                            filter_fields[f'{field_name}'] = visao.sessao_id

                                    qs = Model.objects.filter(**filter_fields)

                                    functions = condition.get('func_exec', {})
                                    for func_name, func_value in functions.items():
                                        if func_name == 'count':
                                            if qs.count() == func_value:
                                                filter_match.append(True)
                                            else:
                                                filter_match.append(False)
                                        elif func_name == 'exists':
                                            filter_match.append(qs.exists() if func_value else not qs.exists())
                            if not all(filter_match):
                                break
                        except Exception as e:
                            logger.error(f'Erro ao avaliar condição de ativação da visão de painel {visao.id}: {e}')
                            filter_match.append(False)

                        if not all(filter_match):
                            break

                    if filter_match and all(filter_match):
                        visoes_changed['activated'].append(visao)
                        visao_ja_ativada = True
                    else:
                        visoes_changed['deactivated'].append(visao)

                    if visao_ja_ativada:
                        break

            #se nenhuma visao foi ativada, ativar a ultima visao
            if not visao_ja_ativada and visao:
                visoes_changed['activated'].append(visao)

    for visao in visoes_changed['deactivated']:
        if visao in visoes_changed['activated']:
            continue
        if visao.active:
            visao.active = False
            visao.save()

    for visao in visoes_changed['activated']:
        if not visao.active:
            visao.active = True
            visao.save()
