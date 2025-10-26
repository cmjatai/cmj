
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

                #visao.refresh_states_from_config_chains()
                activates = visao.config.get('activates', []) or []

                for activate in activates:
                    filter_match = []
                    for appmodels in activate.values():
                        for app_models in appmodels:
                            for app, models in app_models.items():
                                for model_item in models:
                                    for model_name, filter_fields in model_item.items():
                                        Model = apps.get_model(app, model_name)
                                        #fields = Model._meta.get_fields()
                                        #fields_not_relations = dict(filter(lambda item: not item[1], map(lambda f: (f.name, f.is_relation), fields)))
                                        #ff_keys = filter_fields.keys()

                                        qs = Model.objects.filter(**filter_fields)

                                        if sessao_associada_ao_painel and \
                                            Model == sessao_associada_ao_painel._meta.model:
                                            qs = qs.filter(id=sessao_associada_ao_painel.id)

                                        filter_match.append(qs.exists())
                                        if not all(filter_match):
                                            break
                                    if not all(filter_match):
                                        break
                                if not all(filter_match):
                                    break
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