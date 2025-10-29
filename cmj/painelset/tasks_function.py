
#logger = logging.getLogger(__name__)
from celery.utils.log import get_task_logger
from django.apps import apps

from cmj.painelset.models import Evento

logger = get_task_logger(__name__)


def task_refresh_states_from_visaodepainel_function(*args, **kwargs):
    """avaliar visao de painel com base nas chains do campo config de cada visao de painel"""
    # todos os eventos não finalizados

    for evento in Evento.objects.filter(end_real__isnull=True):
        for painel in evento.paineis.all():
            visoes = painel.visoes.all()
            sessao_associada_ao_painel = painel.sessao
            visao_ja_ativada = False

            for visao in visoes:
                if visao_ja_ativada:
                    if visao.active:
                        visao.active = False
                        visao.save()
                    continue

                activates = visao.config.get('activates', []) or []

                for activate in activates:
                    filter_match = []
                    for key, conditions in activate.items():
                        if key != 'activate' or not conditions:
                            continue
                        for condition in conditions:
                            filter_maps = {}
                            for lookup, value in condition.items():
                                app_label, model_name, field_name = lookup.split('__', 2)
                                filter_maps.setdefault((app_label, model_name), {})[field_name] = value

                            for (app_label, model_name), filter_fields in filter_maps.items():
                                Model = apps.get_model(app_label, model_name)
                                fields_relations = dict([
                                    (field.name, field.related_model)
                                    for field in Model._meta.get_fields()
                                    if field.is_relation and hasattr(field, 'related_model')
                                ])
                                for field_name, related_model in fields_relations.items():
                                    if related_model == Evento:
                                        filter_fields[field_name] = evento
                                    elif related_model == painel._meta.model:
                                        filter_fields[field_name] = painel
                                    elif related_model == visao._meta.model:
                                        filter_fields[field_name] = visao
                                    elif related_model == painel.sessao._meta.model:
                                        filter_fields[field_name] = sessao_associada_ao_painel
                                qs = Model.objects.filter(**filter_fields)

                                filter_match.append(qs.exists())
                            if not all(filter_match):
                                break
                        if not all(filter_match):
                            break

                    if filter_match and all(filter_match):
                        if not visao.active:
                            visao.active = True
                            visao.save()
                        visao_ja_ativada = True
                    else:
                        if visao.active:
                            visao.active = False
                            visao.save()
                    if visao_ja_ativada:
                        break

            #se nenhuma visao foi ativada, ativar a ultima visao
            if not visao_ja_ativada and visao:
                if not visao.active:
                    visao.active = True
                    visao.save()