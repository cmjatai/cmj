from collections import OrderedDict
from copy import deepcopy
from datetime import timedelta

from PIL import Image, ImageDraw
from PIL.ImageFont import truetype
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.utils import timezone

from cmj.legacy_sislegis_portal.models import Documento, Tipolei, Itemlei
from sapl.compilacao.models import TextoArticulado,\
    TipoTextoArticulado, TipoDispositivo, STATUS_TA_EDITION, Dispositivo
from sapl.norma.models import NormaJuridica


def _get_registration_key(model):
    return '%s_%s' % (model._meta.app_label, model._meta.model_name)


class Command(BaseCommand):

    _ordem = 0
    graph = OrderedDict()
    arestas_internas = OrderedDict()
    arestas_externas = OrderedDict()

    ta = None

    caracter_desconhecido = []

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
        'subsubitem',
        'subsubsubitem'
    ]

    @property
    def new_ordem(self):
        self._ordem += Dispositivo.INTERVALO_ORDEM
        return self._ordem

    def handle(self, *args, **options):

        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.reset_sequences()
        self.run()
        for cd in self.caracter_desconhecido:
            print(cd)
        self.reset_sequences()

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
        for doc in docs:
            #g[doc_id] = OrderedDict()
            items = Itemlei.objects.filter(id_lei=doc.id).order_by(
                *(['numero', ] + self.fields + ['data_inclusao', ])

            ).values(
                *(
                    [
                        'id',
                        'numero',
                    ]
                    + self.fields +
                    [
                        'nivel',
                        'texto',
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
            self.arestas_internas[item['id']] = {
                'item': item,
                'bloco_alteracao': set(),
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
                print('create_tree erro:', item)

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

        def run_doc(_ID=None):
            docs = Documento.objects.filter(
                assuntos__tipo__in=tipos,
                publicado=True)

            if _ID:
                docs = docs.filter(id=_ID)
            docs = docs.order_by('data_lei')

            related_object_type = ContentType.objects.get_for_model(
                NormaJuridica)

            user = get_user_model().objects.get(pk=1)

            for doc in docs:
                if doc.id not in self.arestas_externas:
                    self.arestas_externas[doc.id] = set()
                if doc.id not in self.graph:
                    self.graph[doc.id] = OrderedDict()

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
                    ta.numero = norma.numero
                    ta.content_object = norma
                    ta.privacidade = STATUS_TA_EDITION
                    ta.editable_only_by_owners = False
                    ta.editing_locked = False
                    ta.created = timezone.now()
                    ta.save()
                else:
                    ta = norma.texto_articulado.first()
                ta.owners.clear()
                ta.owners.add(user)

            self.create_graph(docs)

        def create_arestas(_ID):
            for key, value in self.arestas_internas.items():
                _ID = 0
                if value['item']['id_dono']:
                    if value['item']['id_dono'] in self.arestas_internas:
                        self.arestas_internas[
                            value['item']['id_dono']]['bloco_alteracao'].add(key)
                        self.arestas_externas[value['item']['id_lei']].add(
                            value['item']['id_alterador'])
                    else:
                        return value['item']['id_alterador']
            return 0

        _ID = 0

        if _ID == 0:
            run_doc(_ID=_ID)

        while _ID:
            run_doc(_ID=_ID)
            _ID = create_arestas(_ID)
        else:
            create_arestas(_ID)

        # self.grafh_to_image()
        self.import_graph()

    def import_graph(self):
        print('---- Normas Originais ----')
        for id, dsps in self.graph.items():
            try:
                self.ta = TextoArticulado.objects.get(pk=id)
                print('N.O.', self.ta)
                self._ordem = 0
                roots = self.load_roots(id)
                self.import_subtree(roots, dsps)
            except Exception as e:
                print('N.O. erro:', id, e)

        print('---- Blocos de alteração ----')
        for key, value in self.arestas_internas.items():
            if value['bloco_alteracao']:
                try:
                    print('B.A.', key)
                    self.create_bloco_alteracao(key)
                except Exception as e:
                    print('B.A. erro:', key, e)

        print('---- Compilação ----')
        for id, dsps in self.graph.items():
            try:
                self.ta = TextoArticulado.objects.get(pk=id)
                print('Comp:', self.ta)
                self._ordem = 0
                roots = self.load_roots(id)
                self.import_subtree(roots, dsps, only_originals=False)
            except Exception as e:
                print('Comp erro:', id, e)

    def import_subtree(self, node, subtree, only_originals=True):

        sub_node = node
        last = sub_node
        for n, sub in subtree.items():
            if isinstance(node, dict):
                sub_node = node[
                    'anexos' if sub['type'] == 'anexo' and n else 'corpo1'
                ]

            if sub['item']:
                if sub['item'][0]['id'] in (4986, 27768):
                    sub_node = node['corpo2']

                if sub['item'][0]['id'] in (47043, 48269, 52267):
                    sub_node = node['inicio']

                if only_originals and sub['item'][0]['id_dono']:
                    continue

                _method = 'import_{}'.format(sub['type'])
                if not hasattr(self, _method):
                    _method = 'import_basico'

                try:

                    if sub['item'][0]['id'] == 86519:
                        print(sub['item'][0]['id'])

                    last = getattr(self, _method)(
                        last,
                        sub_node,
                        sub['item'],
                        only_originals=only_originals,
                        ttype=(sub['type'], )
                    )
                except Exception as e:
                    print('import_subtree erro:', sub['item'][0]['id'])
                    raise Exception(e)

            last = self.import_subtree(
                last, sub['subtree'], only_originals=only_originals)
        return last

    def create_bloco_alteracao(self, pk):
        alterador = Dispositivo.objects.filter(id=pk).first()
        if alterador.tipo_dispositivo.class_css == 'artigo':
            alterador = alterador.dispositivos_filhos_set.filter(
                tipo_dispositivo__class_css='caput').first()

        bloco = alterador.dispositivos_filhos_set.filter(
            tipo_dispositivo__class_css='bloco_alteracao').first()

        if bloco:
            return

        td = TipoDispositivo.objects.filter(class_css='bloco_alteracao')[0]

        bloco = Dispositivo()
        bloco.pk = None
        bloco.nivel = bloco.nivel + 1
        bloco.ordem = alterador.criar_espaco(1, local='json_add_in')
        bloco.set_numero_completo([1, 0, 0, 0, 0, 0, ])

        bloco.inicio_vigencia = alterador.ta.data
        bloco.inicio_eficacia = alterador.ta.data

        bloco.fim_vigencia = None
        bloco.fim_eficacia = None
        bloco.auto_inserido = False
        bloco.dispositivo_de_revogacao = True
        bloco.tipo_dispositivo = td
        bloco.dispositivo_subsequente = None
        bloco.dispositivo_substituido = None
        bloco.dispositivo_pai = alterador
        bloco.dispositivo_raiz = alterador.dispositivo_raiz
        bloco.dispositivo_atualizador = None
        bloco.ta = alterador.ta
        bloco.visibilidade = True
        bloco.save()

    def get_bloco_alteracao(self, id_dono):
        alterador = Dispositivo.objects.filter(id=id_dono).first()
        if alterador.tipo_dispositivo.class_css == 'artigo':
            alterador = alterador.dispositivos_filhos_set.filter(
                tipo_dispositivo__class_css='caput').first()

        bloco = alterador.dispositivos_filhos_set.filter(
            tipo_dispositivo__class_css='bloco_alteracao').first()

        return bloco

    def create_dispositivo(self, node_pai, ttype, td, d_old, io, rotulo=None, numero=[]):

        d = Dispositivo.objects.filter(id=io['id']).first()
        if not d:
            d = Dispositivo()
            d.id = io['id']
            if d_old:
                d.ordem = d_old.criar_espaco(1, local='json_add_in')
            else:
                d.ordem = node_pai.criar_espaco(1, local='json_add_next')

        d.contagem_continua = False
        d.nivel = node_pai.nivel + 1
        d.tipo_dispositivo = td
        d.dispositivo_pai = node_pai
        d.dispositivo_raiz = node_pai.dispositivo_raiz if node_pai.dispositivo_raiz else node_pai

        if not numero:
            for t in ttype:
                numero.append(io[t.split()[0]])

            while len(numero) < 6:
                numero.append(0)

        d.set_numero_completo(numero)

        d.ta = self.ta

        d.rotulo = rotulo if rotulo else d.rotulo_padrao()
        d.texto = self.normalize(io['texto'])

        d.inicio_vigencia = self.ta.data
        d.inicio_eficacia = self.ta.data

        if io['id_alterador'] != io['id_lei']:
            d.ta_publicado_id = io['id_alterador']
        d.dispositivo_substituido = d_old

        if io['id_dono']:
            da = self.get_bloco_alteracao(io['id_dono'])
            d.dispositivo_atualizador = da
            d.inicio_vigencia = da.inicio_vigencia
            d.inicio_eficacia = da.inicio_eficacia

        d.visibilidade = True
        d.save()

        if d_old:
            d_old.dispositivo_subsequente = d
            d_old.fim_vigencia = d.inicio_vigencia - timedelta(days=1)
            d_old.fim_eficacia = d.inicio_eficacia - timedelta(days=1)
            d_old.save()
            d.dispositivos_filhos_set.add(
                *list(d_old.dispositivos_filhos_set.all()))

        return d

    def import_basico(self, last, node_pai, items, only_originals, ttype=[]):

        td = TipoDispositivo.objects.filter(class_css=ttype[0])[0]

        d = None

        for io in items:

            d = self.create_dispositivo(
                node_pai, ttype, td, d, io, rotulo=None, numero=[])

            if only_originals:
                break

        return d

    def import_capitulo(self, last, node_pai, items, only_originals, ttype=''):

        while node_pai.tipo_dispositivo.class_css.startswith('capitulo'):
            node_pai = node_pai.dispositivo_pai

        d = self.import_basico(last, node_pai, items, only_originals, ttype=[
                               'capitulo', 'capitulovar'])

        return d

    def import_capitulovar(self, last, node_pai, items, only_originals, ttype=''):
        return self.import_capitulo(last, node_pai, items, only_originals, ttype=ttype)

    def import_secao(self, last, node_pai, items, only_originals, ttype=''):

        while node_pai.tipo_dispositivo.class_css.startswith('secao'):
            node_pai = node_pai.dispositivo_pai

        d = self.import_basico(last, node_pai, items,
                               only_originals, ttype=['secao', 'secaovar'])

        return d

    def import_secaovar(self, last, node_pai, items, only_originals, ttype=''):
        return self.import_secao(last, node_pai, items, only_originals, ttype=ttype)

    def import_artigo(self, last, node_pai, items, only_originals, ttype=''):

        td = TipoDispositivo.objects.filter(class_css='artigo')[0]

        while node_pai.tipo_dispositivo.class_css.startswith('artigo'):
            node_pai = node_pai.dispositivo_pai

        a = None
        caput_old = None
        for io in items:
            try:
                caput = Dispositivo.objects.filter(id=io['id']).first()
                if not a:
                    if not caput:
                        a = Dispositivo()
                        a.ordem = node_pai.criar_espaco(
                            1, local='json_add_next')

                        a.contagem_continua = True
                        a.nivel = node_pai.nivel + 1
                        a.tipo_dispositivo = td
                        a.dispositivo_pai = node_pai
                        a.dispositivo_raiz = node_pai.dispositivo_raiz \
                            if node_pai.dispositivo_raiz else node_pai

                        a.dispositivo0 = io['artigo']
                        a.dispositivo1 = io['artigovar']
                        a.dispositivo2 = io['artigovarvar']

                        a.ta = self.ta
                        a.inicio_vigencia = self.ta.data
                        a.inicio_eficacia = self.ta.data
                        a.rotulo = a.rotulo_padrao()

                        # associação para inclusões por norma alteradora

                        if io['id_alterador'] != io['id_lei']:
                            a.ta_publicado_id = io['id_alterador']

                        if io['id_dono']:
                            da = self.get_bloco_alteracao(io['id_dono'])
                            a.dispositivo_atualizador = da
                            a.inicio_vigencia = da.inicio_vigencia
                            a.inicio_eficacia = da.inicio_eficacia

                        a.visibilidade = False
                        a.save()

                if not caput:
                    caput = Dispositivo()
                    caput.id = io['id']
                    if not caput_old:
                        caput.ordem = a.criar_espaco(1, local='json_add_in')
                    else:
                        caput.ordem = caput_old.criar_espaco(
                            1, local='json_add_next')
                    caput.auto_inserido = True
                else:
                    a = caput.dispositivo_pai

                td_caput = TipoDispositivo.objects.filter(class_css='caput')[0]
                caput.tipo_dispositivo = td_caput
                caput.nivel = a.nivel + 1
                caput.dispositivo_pai = a
                caput.dispositivo_raiz = a.dispositivo_raiz

                caput.ta = self.ta
                caput.inicio_vigencia = self.ta.data
                caput.inicio_eficacia = self.ta.data
                caput.rotulo = caput.rotulo_padrao()
                caput.texto = self.normalize(io['texto'])

                if io['id_alterador'] != io['id_lei']:
                    caput.ta_publicado_id = io['id_alterador']
                caput.dispositivo_substituido = caput_old
                if io['id_dono']:
                    da = self.get_bloco_alteracao(io['id_dono'])
                    caput.dispositivo_atualizador = da
                    caput.inicio_vigencia = da.inicio_vigencia
                    caput.inicio_eficacia = da.inicio_eficacia

                caput.visibilidade = True
                caput.save()

                if only_originals:
                    break

                if caput_old:
                    caput_old.dispositivo_subsequente = caput
                    caput_old.fim_vigencia = caput.inicio_vigencia - \
                        timedelta(days=1)
                    caput_old.fim_eficacia = caput.inicio_eficacia - \
                        timedelta(days=1)
                    caput_old.save()
                    caput.dispositivos_filhos_set.add(
                        *list(caput_old.dispositivos_filhos_set.all()))

                caput_old = caput
            except Exception as e:
                print('import_artigo erro:', io)
                print('import_artigo erro:', e)

        return a

    def import_artigovar(self, last, node_pai, items, only_originals, ttype=''):
        return self.import_artigo(last, node_pai, items, only_originals, ttype=ttype)

    def import_artigovarvar(self, last, node_pai, items, only_originals, ttype=''):
        return self.import_artigo(last, node_pai, items, only_originals, ttype=ttype)

    def import_paragrafo(self, last, node_pai, items, only_originals, ttype=''):

        td = TipoDispositivo.objects.filter(
            class_css__icontains='paragrafo')[0]

        d = None

        for io in items:

            if io['nivel'] == 1001:
                rotulo = 'Parágrafo Único'
                io['paragrafo'] = 1
            else:
                rotulo = '§ {}º'.format(io['paragrafo'])

            numero = [io['paragrafo'], 0, 0, 0, 0, 0]

            if io['id'] in (46773, 63405):
                numero[0] = 2
            if io['id'] in (54010, 57991, 62879, 68520, 84312,
                            20842, 18853, 18823, 15815, 24952,
                            37877, 84386, 36497, 36511, 25254,
                            36561, 36598, 16167, 18864, 36852,
                            17111, 79237, 2780, 47023, 8600, 35828,
                            8685, 36359, 11383, 51848, 9799, 58320,
                            6007, 63829, 17553, 41584, 78929, 55000,
                            60420, 64982, 86262, 83234, 88413
                            ):
                numero[0] = 3
            elif io['id'] in (57838, 56855, 9746, 73697, 64452,
                              25821, 36872, 81696, 83237):
                numero[0] = 4
            elif io['id'] in (5243, 18902, 21912, 24456, 35958,
                              36224, 36259, 24815, 26090, 84429,
                              24505):
                numero[0] = 5
            elif io['id'] in ():
                numero[0] = 6
            elif io['id'] in (36333, 37867):
                numero[0] = 7
            elif io['id'] in (57113, 56351):
                numero[0] = 8
            elif io['id'] in (36539, ):
                numero[0] = 9
            elif io['id'] in (84420, ):
                numero[0] = 13

            try:
                d = self.create_dispositivo(
                    node_pai,
                    ttype,
                    td,
                    d,
                    io,
                    rotulo,
                    numero=numero)
            except Exception as e:
                print('erro de parágrafo:', io['id'], io['id_lei'])

            if only_originals:
                break

        return d

    def import_inciso(self, last, node_pai, items, only_originals, ttype=''):

        if node_pai.tipo_dispositivo.class_css == 'artigo':
            node_pai = node_pai.dispositivos_filhos_set.filter(
                tipo_dispositivo__class_css='caput').first()

        while node_pai.tipo_dispositivo.class_css.startswith('inciso'):
            node_pai = node_pai.dispositivo_pai

        d = self.import_basico(last, node_pai, items,
                               only_originals,
                               ttype=['inciso indent', 'incisovar', 'incisovarvar'])

        return d

    def import_incisovar(self, last, node_pai, items, only_originals, ttype=''):
        return self.import_inciso(last, node_pai, items, only_originals, ttype=ttype)

    def import_incisovarvar(self, last, node_pai, items, only_originals, ttype=''):
        return self.import_inciso(last, node_pai, items, only_originals, ttype=ttype)

    def import_alinea(self, last, node_pai, items, only_originals, ttype=''):

        if node_pai.tipo_dispositivo.class_css == 'artigo':
            node_pai = node_pai.dispositivos_filhos_set.filter(
                tipo_dispositivo__class_css='caput').first()

        d = self.import_basico(last, node_pai, items,
                               only_originals,
                               ttype=['alinea indent'])

        return d

    def import_item(self, last, node_pai, items, only_originals, ttype=''):

        if node_pai.tipo_dispositivo.class_css == 'artigo':
            node_pai = node_pai.dispositivos_filhos_set.filter(
                tipo_dispositivo__class_css='caput').first()

        while node_pai.tipo_dispositivo.class_css.endswith('item'):
            node_pai = node_pai.dispositivo_pai

        d = self.import_basico(last, node_pai, items,
                               only_originals,
                               ttype=['item indent',
                                      'subitem',
                                      'subsubitem',
                                      'subsubsubitem'])

        return d

    def import_subitem(self, last, node_pai, items, only_originals, ttype=''):
        return self.import_item(last, node_pai, items, only_originals, ttype=ttype)

    def import_subsubitem(self, last, node_pai, items, only_originals, ttype=''):
        return self.import_item(last, node_pai, items, only_originals, ttype=ttype)

    def import_subsubsubitem(self, last, node_pai, items, only_originals, ttype=''):
        return self.import_item(last, node_pai, items, only_originals, ttype=ttype)

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
            e.texto = self.normalize(ta.ementa)
            e.dispositivo_pai = a
            e.save()

            a.pk = None  # articulação do corpo do texto
            a.nivel = 0
            a.ordem = self.new_ordem
            a.set_numero_completo([2, 0, 0, 0, 0, 0, ])
            a.save()

            a.pk = None  # articulação2 do corpo do texto
            a.nivel = 0
            a.ordem = self.new_ordem
            a.set_numero_completo([3, 0, 0, 0, 0, 0, ])
            a.save()

            a.pk = None  # articulação assinatura
            a.nivel = 0
            a.ordem = self.new_ordem
            a.set_numero_completo([4, 0, 0, 0, 0, 0, ])
            a.save()

            a.pk = None  # articulação para anexos - excluir no final se vazio
            a.nivel = 0
            a.ordem = self.new_ordem
            a.set_numero_completo([5, 0, 0, 0, 0, 0, ])
            a.save()

        roots = Dispositivo.objects.order_by(
            'ordem').filter(nivel=0, ta_id=ta.id)

        roots = {
            'inicio':  roots[0],
            'corpo1': roots[1],
            'corpo2': roots[2],
            'assinatura': roots[3],
            'anexos': roots[4]
        }

        return roots

    def normalize(self, texto):
        white_char = ' ãâáàäeêéèëiîíìïõôóòöuûúùüç' + \
            'ÃÂÁÀÄEÊÉÈËIÎÍÌÏÕÔÓÒÖUÛÚÙÜÇ' + \
            'abcdefghijklmnopqrstuvwxyz' + \
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + \
            '0123456789' + \
            'ºª§/-_,.;:!@#$%*()?[]~"<>=\r\n\t²³°&+|' + "'"

        black_char = {
            '´': "'",
            '`': "'",
            '': '-',
            '': '"',
            '': '',
            '': "'",
            '·': " ",
            '”': '"',
            '“': '"',
            '½': '1/2',
            '’': '"',
            '‘': '"',
            '¼': '1/4'
        }

        for c in texto:
            if c in black_char:
                texto.replace(c, black_char[c])
            elif ord(c) in (160, 173, 172, 145, 151, 92, 8211):
                texto.replace(c, '-')
            elif c not in white_char:
                self.caracter_desconhecido.append((ord(c), c, texto))

        return texto

    def grafh_to_image(self):

        #d.text((10, 10), "Hello World", fill=(0, 0, 0), font=f)

        ae = self.arestas_externas
        segmentos = []
        for k, v in ae.items():
            for a in v:
                segmentos.append(
                    [
                        0, list(ae.keys()).index(k),
                        0, list(ae.keys()).index(a)

                    ]
                )

        def cmp_to_key(mycmp):
            'Convert a cmp= function into a key= function'
            class K:
                def __init__(self, obj, *args):
                    self.obj = obj

                def __lt__(self, other):
                    return mycmp(self.obj, other.obj) < 0

                def __gt__(self, other):
                    return mycmp(self.obj, other.obj) > 0

                def __eq__(self, other):
                    return mycmp(self.obj, other.obj) == 0

                def __le__(self, other):
                    return mycmp(self.obj, other.obj) <= 0

                def __ge__(self, other):
                    return mycmp(self.obj, other.obj) >= 0

                def __ne__(self, other):
                    return mycmp(self.obj, other.obj) != 0
            return K

        def sort_seg(a, b):
            if a[3] - a[1] > b[3] - b[1]:
                return 1
            if a[3] - a[1] < b[3] - b[1]:
                return -1

            if a[1] > b[1]:
                return 1
            if a[1] < b[1]:
                return -1

            if a[3] > b[3]:
                return 1
            if a[3] < b[3]:
                return -1
            return 0
        print(segmentos)
        segmentos.sort(key=cmp_to_key(sort_seg))
        print(segmentos)

        """
        x_max = 0
        for p in seg:
            x = 0
            for pn in seg:
                if p == pn:
                    continue

                if pn[1] < p[3] and pn[3] > p[1] and pn[0] == p[0]:
                    x += 1
                    pn[0] = pn[2] = x

                    if x > x_max:
                        x_max = x"""

        ws = segmentos
        segmentos = [[]]
        while ws:
            s = ws.pop(0)
            for gs in segmentos:
                ok = True
                for i in gs:
                    ok = i[1] < s[1] and i[3] < s[1] or i[1] > s[3] and i[3] > s[3]
                    if not ok:
                        break

                if ok:
                    gs.append(s)
                    break
            if segmentos[-1]:
                segmentos.append([])

        x = 0
        seg = []
        for gs in segmentos:
            for s in gs:
                s[0] = x
                s[2] = x
                seg.append(s)
            x += 1
        x_max = x
        my = 50
        mx = 80

        x = mx
        y = my
        r = 5
        dx = 50
        dy = 10
        img = Image.new('RGB', (x_max * dx * 2 + mx, len(self.graph) * 50),
                        color=(255, 255, 255))

        f = truetype(
            font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            size=15)
        d = ImageDraw.Draw(img)

        pos = 0
        for node, value in self.graph.items():
            d.ellipse((x - r, y - r, x + r, y + r), fill=(0, 0, 0, 255))
            d.text((20, y - r), str(node), fill=(0, 0, 0), font=f)
            #d.text((mx, y + r), str(pos), fill=(0, 0, 0), font=f)
            y += 50 - dy
            pos += 1

        for p in seg:
            y = my - dy
            pv = (
                p[0] * dx + mx + dx,
                p[1] * y + y + 2 * r,
                p[2] * dx + mx + dx,
                p[3] * y + y + 2 * r  # - p[0] * r * 4
            )
            ph1 = (
                mx,
                p[1] * y + y + 2 * r,
                p[0] * dx + mx + dx,
                p[1] * y + y + 2 * r,
            )

            ph2 = (
                mx,
                p[3] * y + y + 2 * r,
                p[2] * dx + mx + dx,
                p[3] * y + y + 2 * r  # - p[0] * r * 4,
            )

            d.line(ph1, fill=128, width=1)
            d.line(pv, fill=128, width=1)
            d.line(ph2, fill=128, width=1)

        img.save("/home/leandro/teste.png")
