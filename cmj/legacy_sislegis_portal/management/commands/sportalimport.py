from collections import OrderedDict
from copy import deepcopy

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from django.utils import timezone
from sapl.compilacao.models import Dispositivo, TextoArticulado,\
    STATUS_TA_PUBLIC, TipoTextoArticulado, TipoDispositivo, STATUS_TA_EDITION
from sapl.norma.models import NormaJuridica

from cmj.legacy_sislegis_portal.models import Documento, Tipolei, Itemlei


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    _ordem = 0
    graph = OrderedDict()
    index = OrderedDict()
    fields = [
        'anexo',
        'parte',
        'livro',
        'titulo',
        'capitulo',
        'capitulovar',
        'secao',
        'secaovar',
        'subsecao',
        'itemsecao',
        'artigo',
        'artigovar',
        'artigovarvar',
        'paragrafo',
        'inciso',
        'incisovar',
        'incisovarvar',
        'alinea',
        'item',
        'subitem',
        'subsubitem'
    ]

    @property
    def new_ordem(self):
        self._ordem += Dispositivo.INTERVALO_ORDEM
        return self._ordem

    def handle(self, *args, **options):
        # self.reset_sequences()
        self.run()
        # self.reset_sequences()

    def reset_sequences(self):

        for model in apps.get_app_config('compilacao').get_models():

            query = """SELECT setval(pg_get_serial_sequence('"%(app_model_name)s"','id'),
                        coalesce(max("id"), 1), max("id") IS NOT null) 
                        FROM "%(app_model_name)s";
                    """ % {
                'app_model_name': _get_registration_key(model)
            }

            if model == Dispositivo and not Dispositivo.objects.exists():
                query = """SELECT setval(pg_get_serial_sequence('"%(app_model_name)s"','id'),
                            coalesce(max("id"), 100000), max("id") IS NOT null) 
                            FROM "%(app_model_name)s";
                        """ % {
                    'app_model_name': _get_registration_key(model)
                }

            with connection.cursor() as cursor:
                cursor.execute(query)
                # get all the rows as a list
                rows = cursor.fetchall()
                print(rows)

    def create_graph(self, docs):
        g = self.graph
        for doc_id in docs:
            g[doc_id] = OrderedDict()
            items = Itemlei.objects.filter(id_lei=doc_id).order_by(
                *(['numero', ] + self.fields + ['data_inclusao', ])

            ).values(
                *(
                    [
                        'id',
                        'numero',
                    ]
                    + self.fields +
                    [
                        'data_inclusao',
                        'id_lei',
                        'id_alterador',
                        'id_dono',
                    ]
                )
            )

            self.create_tree(items)

    def create_tree(self, items):
        g = self.graph
        t = None

        for item in items:
            self.index[item['id']] = {
                'item': item,
                'bloco_alteracao': [],
            }
            if t is None:
                t = g[item['id_lei']]

            fields = self.fields[::-1]

            while fields and not item[fields[0]]:
                del fields[0]

            try:
                self.put_node(
                    t, item, fields[::-1]
                )
            except:
                print(item)

    def put_node(self, subtree, item, _fields):
        f = _fields[0]
        if item[f] not in subtree:
            st = subtree[item[f]] = {
                'type': f,
                'item': [],
                'subtree': OrderedDict()
            }
        else:
            st = subtree[item[f]]

        if len(_fields) == 1:
            st['item'].append(item)
        else:
            self.put_node(st['subtree'], item, _fields[1:])

    def run(self):
        q = Q(id__gte=28) | Q(id=27) | Q(id=5) | Q(id=4)
        tipos = Tipolei.objects.exclude(q).order_by('id')

        # for tipo in tipos:
        #    print(tipo.pk, tipo.descr)

        docs = Documento.objects.filter(
            assuntos__tipo__in=tipos,
            publicado=True).order_by('data_lei')

        related_object_type = ContentType.objects.get_for_model(NormaJuridica)

        user = get_user_model().objects.get(pk=1)

        """for doc in docs:
            if not NormaJuridica.objects.filter(id=doc.id).exists():
                continue

            norma = NormaJuridica.objects.get(id=doc.id)

            assert norma.texto_articulado.count() <= 1, \
                "Norma {} - {} com mais de 1 T.A.".format(norma.id, norma)

            if not norma.texto_articulado.exists():
                ta = TextoArticulado()
                ta.id = norma.id
                ta.tipo_ta = TipoTextoArticulado.objects.filter(
                    content_type=related_object_type).first()
                ta.data = norma.data
                ta.ementa = norma.ementa
                ta.observacao = norma.observacao
                ta.ano = norma.ano
                ta.content_object = norma
                ta.privacidade = STATUS_TA_EDITION
                ta.editable_only_by_owners = False
                ta.editing_locked = False
                ta.created = timezone.now()
                ta.save()
            else:
                ta = norma.texto_articulado.first()
            ta.owners.clear()
            ta.owners.add(user)"""

        self.create_graph(docs.values_list('id', flat=True))

        for key, value in self.index.items():
            if value['item']['id_dono']:
                self.index[value['item']['id_dono']
                           ]['bloco_alteracao'].append(key)

        self.import_graph()

    def import_graph(self):

        for id, dsps in self.graph.items():
            self._ordem = 0
            roots = self.load_roots(id)
            self.import_subtree(roots, dsps)

        for id, dsps in self.graph.items():
            self._ordem = 0
            roots = self.load_roots(id)
            self.import_subtree(roots, dsps, only_originals=False)

    def import_subtree(self, node, subtree, only_originals=True):

        for n, sub in subtree.items():
            sub_node = node
            if isinstance(node, dict):
                sub_node = sub_node[
                    'anexos' if sub['type'] == 'anexo' and n else 'corpo'
                ]

            if sub['item']:
                _method = 'import_{}'.format(sub['type'])
                _method = _method if hasattr(
                    self, _method) else 'import_basico'

                sub_node = getattr(self, _method)(
                    sub_node,
                    sub['item'],
                    only_originals=only_originals)

            self.import_subtree(sub_node, sub['subtree'])

    def import_basico(self, node, items, only_originals):
        item_original = items[0]
        items_alterados = items[1:]

    def import_capitulo(self, node, items, only_originals):
        item_original = items[0]
        items_alterados = items[1:]

    def load_roots(self, id):
        ta = TextoArticulado.objects.get(id=id)
        if not ta.dispositivos_set.exists():
            # articulação base.
            td = TipoDispositivo.objects.filter(class_css='articulacao')[0]
            a = Dispositivo()
            a.nivel = 0
            a.ordem = self.new_ordem
            a.ordem_bloco_atualizador = 0
            a.set_numero_completo([1, 0, 0, 0, 0, 0, ])
            a.ta = ta
            a.tipo_dispositivo = td
            a.inicio_vigencia = ta.data
            a.inicio_eficacia = ta.data
            a.save()

            td = TipoDispositivo.objects.filter(class_css='ementa')[0]
            e = Dispositivo()
            e.nivel = 1
            e.ordem = self.new_ordem
            e.ordem_bloco_atualizador = 0
            e.set_numero_completo([1, 0, 0, 0, 0, 0, ])
            e.ta = ta
            e.tipo_dispositivo = td
            e.inicio_vigencia = ta.data
            e.inicio_eficacia = ta.data
            e.texto = ta.ementa
            e.dispositivo_pai = a
            e.save()

            a.pk = None  # articulação do corpo do texto
            a.nivel = 0
            a.ordem = self.new_ordem
            a.set_numero_completo([2, 0, 0, 0, 0, 0, ])
            a.save()

            a.pk = None  # articulação assinatura
            a.nivel = 0
            a.ordem = self.new_ordem
            a.set_numero_completo([3, 0, 0, 0, 0, 0, ])
            a.save()

            a.pk = None  # articulação para anexos - excluir no final se vazio
            a.nivel = 0
            a.ordem = self.new_ordem
            a.set_numero_completo([4, 0, 0, 0, 0, 0, ])
            a.save()

        roots = Dispositivo.objects.order_by(
            'ordem').filter(nivel=0, ta_id=ta.id)

        roots = {
            'inicio':  roots[0],
            'corpo': roots[1],
            'assinatura': roots[2],
            'anexos': roots[3]
        }

        return roots
