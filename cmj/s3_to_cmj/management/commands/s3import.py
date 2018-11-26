from copy import deepcopy

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection
from sapl.materia.models import MateriaLegislativa, DocumentoAcessorio
from sapl.norma.models import NormaJuridica
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo
from cmj.s3_to_cmj import mapa
from cmj.s3_to_cmj.migracao_documentos_via_request import migrar_docs_por_ids


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    def handle(self, *args, **options):
        # self.clear()
        self.run()
        self.reset_sequences()
        # self.migrar_documentos()
        # self.list_models_with_relation()

    def migrar_documentos(self):
        for model in [
            Parlamentar,
            MateriaLegislativa,
            DocumentoAcessorio,
            NormaJuridica,
            DocumentoAdministrativo,
            DocumentoAcessorioAdministrativo,
        ]:
            erros = self.migrar_docs_por_ids(model)

        for e in erros:
            print(e)

    def clear(self, models=None):
        mapa_for_clear = deepcopy(mapa.mapa)
        mapa_for_clear.reverse()

        mapa_for_clear = mapa_for_clear[:-1]

        def clear_model(model):
            if models and model not in models:
                return

            query = 'delete FROM "%(app_model_name)s";' % {
                'app_model_name': _get_registration_key(model)
            }

            with connection.cursor() as cursor:
                cursor.execute(query)

        for item in mapa_for_clear:
            print('Limpando...', item['s31_model']._meta.object_name)

            for key, rel in item['s31_model']._meta.fields_map.items():
                if hasattr(rel, 'one_to_many') and rel.one_to_many:
                    clear_model(rel.related_model)

            clear_model(item['s31_model'])

    def migrar_docs_por_ids(self, model):
        return migrar_docs_por_ids(model)

    def run(self):
        for item in mapa.mapa[1:]:

            print('Migrando...', item['s31_model']._meta.object_name)
            old_list = item['s30_model'].objects.all()
            if 'ind_excluido' in item['fields']:
                old_list_excluidos = list(old_list.filter(
                    ind_excluido=1).values_list(
                        item['fields']['id'], flat=True))
                item['s31_model'].objects.filter(
                    id__in=old_list_excluidos).delete()

                old_list = old_list.filter(ind_excluido=0)

            count_old_list = old_list.count()
            count = 0

            if hasattr(self, 'sync') and self.sync and count_old_list > 100:
                old_list = old_list.order_by('-{}'.format(
                    item['fields']['id'])
                )[:int(count_old_list * self.sync) + 1]

            for old in old_list:
                count += 1

                if count % 100 == 0:
                    print('Migrando...',
                          item['s31_model']._meta.object_name,
                          count, 'de', count_old_list)

                if hasattr(old, 'ind_excluido') and old.ind_excluido is None:
                    print(old.__dict__)
                    return

                novo = False
                try:
                    new = item['s31_model'].objects.get(
                        pk=getattr(old, item['fields']['id']))
                except:
                    novo = True
                    new = item['s31_model']()

                for new_field, old_field in item['fields'].items():
                    if new_field == 'ind_excluido':
                        continue
                    setattr(new, new_field, getattr(old, old_field))

                try:
                    if 'adjust' in item:
                        item['adjust'](new, old)

                    if novo:
                        new.save()
                    else:
                        new.save()
                # except IntegrityError as ie:
                #    pass
                except Exception as e:
                    self.print_erro(e, item, new)

    def reset_sequences(self):
        def reset_id_model(model):

            query = """SELECT setval(pg_get_serial_sequence('"%(app_model_name)s"','id'),
                        coalesce(max("id"), 1), max("id") IS NOT null) 
                        FROM "%(app_model_name)s";
                    """ % {
                'app_model_name': _get_registration_key(model)
            }

            with connection.cursor() as cursor:
                cursor.execute(query)
                # get all the rows as a list
                rows = cursor.fetchall()
                print(rows)

        for model in mapa.mapa[0]['s31_model']:
            if not isinstance(model, str):
                reset_id_model(model)

        for model in mapa.mapa[1:]:
            reset_id_model(model['s31_model'])

    def list_models_with_relation(self):
        sapl_apps = apps.get_app_configs()

        for app in sapl_apps:
            if app.name.startswith('sapl.') and app.name not in (
                    'sapl.s3',
                    'sapl.compilacao'):
                for name, model in app.models.items():
                    if self.is_model_mapeado(model):
                        continue
                    model_with_fk = []
                    for field in model._meta.fields:
                        if field.is_relation:
                            model_with_fk.append(field)

                    print(app.label,
                          model._meta.object_name,
                          len(model_with_fk))

    def is_model_mapeado(self, model):
        for item in mapa.mapa:
            if item['s31_model'] == model:
                return True
        for m in mapa.mapa[0]['s31_model']:
            if m == model or m == model._meta.object_name:
                return True

        return False

    def print_erro(self, e, item, new):
        detail_de_master_excluido = (
            '(parlamentar_id)=(18)',
            '(parlamentar_id)=(35)',
            '(parlamentar_id)=(42)',
            '(parlamentar_id)=(40)',
            '(parlamentar_id)=(41)',
            '(parlamentar_id)=(38)',
            '(parlamentar_id)=(39)',
            '(parlamentar_id)=(37)',
            '(parlamentar_id)=(28)',
            '(sessao_plenaria_id)=(409)',
            '(tipo_id)=(2) is not present in table "sessao_tipoexpediente"',
            ' "unidade_tramitacao_destino_id" violates not-null constraint',
            '"materia_autoria"',
            '"materia_anexada"',
            '"materia_tramitacao"',
            '"sessao_expedientemateria" violates foreign '
            'key constraint "sessao_exp_materia_id_',
            '"sessao_registrovotacao" violates foreign key '
            'constraint "sessao_reg_materia_id',




        )
        msg_localizada = False

        for teste in detail_de_master_excluido:
            if teste in str(e):
                msg_localizada = True
        if not msg_localizada:
            print(
                'ERRO:', item['s31_model']._meta.object_name, new.id, e)
