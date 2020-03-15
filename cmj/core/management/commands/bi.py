import logging

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.db.models.signals import post_delete, post_save
from django.utils.translation import ugettext_lazy as _
from pdfrw.pdfreader import PdfReader

from cmj.core.models import Bi
from cmj.diarios.models import DiarioOficial
from cmj.sigad.models import VersaoDeMidia, Documento, Midia
from cmj.utils import run_sql
from sapl.materia.models import MateriaLegislativa, Tramitacao
from sapl.norma.models import NormaJuridica, AnexoNormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    TramitacaoAdministrativo


class Command(BaseCommand):

    def handle(self, *args, **options):
        post_delete.disconnect(dispatch_uid='sapl_post_delete_signal')
        post_save.disconnect(dispatch_uid='sapl_post_save_signal')
        post_delete.disconnect(dispatch_uid='cmj_post_delete_signal')
        post_save.disconnect(dispatch_uid='cmj_post_save_signal')

        self.logger = logging.getLogger(__name__)

        self.run_bi()

    def run_bi(self):
        self.run_bi_files()

    def run_bi_files(self):
        reset_errors_count_page = False
        models = [
            {
                'model': MateriaLegislativa,
                'file_field': 'texto_original',
                'hook': 'run_bi_materias_legislativas',
                'results': {},
                'reset_errors_count_page': reset_errors_count_page
            },
            {
                'model': NormaJuridica,
                'file_field': 'texto_integral',
                'hook': 'run_bi_normajuridica',
                'results': {},
                'reset_errors_count_page': reset_errors_count_page
            },
            {
                'model': AnexoNormaJuridica,
                'file_field': 'anexo_arquivo',
                'hook': '',
                'reset_errors_count_page': reset_errors_count_page
            },
            {
                'model': DocumentoAdministrativo,
                'file_field': 'texto_integral',
                'hook': 'run_bi_documentoadministrativo',
                'results': {},
                'reset_errors_count_page': reset_errors_count_page
            },
            {
                'model': DiarioOficial,
                'file_field': 'arquivo',
                'hook': 'run_bi_diariooficial',
                'results': {},
                'reset_errors_count_page': reset_errors_count_page
            },
            {
                'model': VersaoDeMidia,
                'file_field': 'file',
                'hook': 'run_bi_midias_imagens',
                'results': {},
                'reset_errors_count_page': reset_errors_count_page
            },
            {
                'model': Documento,
                'hook': 'run_bi_sigad_documento',
                'reset_errors_count_page': reset_errors_count_page,
                'results': {},
            },
            {
                'model': Tramitacao,
                'hook': 'run_bi_tramitacao',
                'reset_errors_count_page': reset_errors_count_page,
                'results': {},
            },
        ]

        # Bi.objects.all().delete()

        for mt in models:  # mt = metadata
            if not mt['hook']:
                continue

            if mt['hook'] != 'run_bi_tramitacao':
                continue

            if mt['reset_errors_count_page']:
                run_sql(
                    '''update {} 
                            set _paginas = 0 
                            where _paginas = -1;'''.format(
                        '%s_%s' % (mt['model']._meta.app_label,
                                   mt['model']._meta.model_name)
                    )
                )

            getattr(self, mt['hook'])(mt)

            for ano, value in mt['results'].items():

                bi, created = Bi.objects.get_or_create(
                    ano=ano,
                    content_type=ContentType.objects.get_for_model(
                        mt['model']
                    )
                )

                bi.results = value
                bi.save()

        print('Concluído')

    def run_count_pages_from_file(self, filefield):
        count_pages = 0
        try:
            path = filefield.file.name
            pdf = PdfReader(path)
            count_pages += len(pdf.pages)
            filefield.file.close()
        except Exception as e:
            pass
            # print(e)
        else:
            return count_pages

    def run_bi_tramitacao(self, mt):
        trm = Tramitacao.objects.all().order_by('id')

        r = {}
        for t in trm:
            if not t.data_tramitacao:
                continue
            if t.data_tramitacao.year in r:
                r[t.data_tramitacao.year].append(t)
                continue
            r[t.data_tramitacao.year] = [t, ]

        trm = TramitacaoAdministrativo.objects.filter(
            documento__workspace_id=22
        ).order_by('id')

        for t in trm:
            if not t.data_tramitacao:
                continue
            if t.data_tramitacao.year in r:
                r[t.data_tramitacao.year].append(t)
                continue
            r[t.data_tramitacao.year] = [t, ]

        total = 0
        results = mt['results']
        for k, v in r.items():
            if k not in results:
                results[k] = {}

            for t in v:

                u = 0
                if u not in results[k]:
                    results[k][u] = {}

                ru = results[k][u]

                y = t.data_tramitacao.year

                if 'Tramitações' not in ru:
                    ru['Tramitações'] = {}

                if y not in ru['Tramitações']:
                    ru['Tramitações'][y] = {'count': 0}

                ru['Tramitações'][y]['count'] += 1

    def run_bi_midias_imagens(self, mt):
        midias = Midia.objects.filter(
            documento__tipo=Documento.TPD_IMAGE).order_by('id')

        r = {}
        for m in midias:
            if not m.documento.created:
                continue
            if m.documento.created.year in r:
                r[m.documento.created.year].append(m)
                continue
            r[m.documento.created.year] = [m, ]

        total = 0
        results = mt['results']
        for k, v in r.items():
            if k not in results:
                results[k] = {}

            for m in v:

                u = 0
                if u not in results[k]:
                    results[k][u] = {}

                ru = results[k][u]

                y = m.documento.created.year

                tipo = m.documento.get_tipo_display()
                if m.documento.tipo == 900:
                    tipo = 'Imagens'

                if tipo not in ru:
                    ru[tipo] = {}

                if y not in ru[tipo]:
                    ru[tipo][y] = {'count': 0}

                ru[tipo][y]['count'] += 1

    def run_bi_sigad_documento(self, mt):
        docs = Documento.objects.filter(
            tipo__in=Documento.TDs).order_by('id')

        r = {}
        for d in docs:
            if not d.public_date:
                continue
            if d.public_date.year in r:
                r[d.public_date.year].append(d)
                continue
            r[d.public_date.year] = [d, ]

        total = 0
        results = mt['results']
        for k, v in r.items():
            if k not in results:
                results[k] = {}

            for doc in v:

                u = 0
                if u not in results[k]:
                    results[k][u] = {}

                ru = results[k][u]

                y = doc.public_date.year

                tipo = doc.get_tipo_display()
                if doc.tipo == 0:
                    tipo = 'Notícias'

                if tipo not in ru:
                    ru[tipo] = {}

                if y not in ru[tipo]:
                    ru[tipo][y] = {'total': 0}

                ru[tipo][y]['total'] += 1

    def run_bi_documentoadministrativo(self, mt):
        docs = DocumentoAdministrativo.objects.filter(
            workspace_id=22  # área pública
        ).order_by('id')

        ano_cadastro = 2008
        r = {}
        for d in docs:
            if d.ano <= ano_cadastro:
                r[ano_cadastro].append(d)
                continue
            ano_cadastro = d.ano
            r[ano_cadastro] = [d, ]

        total = 0
        results = mt['results']
        for k, v in r.items():  # ano, lista de materias cadastradas no ano
            if k not in results:
                results[k] = {}
                #results[k]['tramitacao'] = 0

            for doc in v:

                u = 0
                if u not in results[k]:
                    results[k][u] = {}
                    results[k][u]['Documentos Administrativos'] = {}
                    results[k][u]['Documentos Acessórios'] = {}

                ru = results[k][u]

                if doc.ano not in ru['Documentos Administrativos']:
                    ru['Documentos Administrativos'][doc.ano] = {
                        'total': 0,
                        'tramitacao': 0,
                        'paginas': 0,
                        'ep': []
                    }

                ru['Documentos Administrativos'][doc.ano]['total'] += 1
                ru['Documentos Administrativos'][doc.ano]['tramitacao'] += doc.tramitacaoadministrativo_set.count()

                if doc.ano not in ru['Documentos Acessórios']:
                    ru['Documentos Acessórios'][doc.ano] = {
                        'total': 0, 'paginas': 0, 'ep': []
                    }

                if doc.documentoacessorioadministrativo_set.exists():
                    ru['Documentos Acessórios'][doc.ano]['total'] += doc.documentoacessorioadministrativo_set.count()

                try:
                    ru['Documentos Administrativos'][doc.ano]['paginas'] += doc.paginas
                except:
                    ru['Documentos Administrativos'][doc.ano]['ep'].append(
                        doc.id)

                for da in doc.documentoacessorioadministrativo_set.all():
                    try:
                        ru['Documentos Acessórios'][doc.ano]['paginas'] += da.paginas
                    except:
                        ru['Documentos Acessórios'][doc.ano]['ep'].append(
                            da.id)

    def run_bi_materias_legislativas(self, mt):
        materias = MateriaLegislativa.objects.order_by('id')

        ano_cadastro = 2008
        r = {}
        for m in materias:
            if m.ano <= ano_cadastro:
                r[ano_cadastro].append(m)
                continue
            ano_cadastro = m.ano
            r[ano_cadastro] = [m, ]

        total = 0
        results = mt['results']
        for k, v in r.items():  # ano, lista de materias cadastradas no ano
            if k not in results:
                results[k] = {}

            for materia in v:

                u = materia.user_id if materia.ano == 2020 else (
                    materia.user_id if materia.user_id else 0)
                if u not in results[k]:
                    results[k][u] = {}
                    results[k][u]['Matérias Legislativas'] = {}
                    results[k][u]['Documentos Acessórios'] = {}

                ru = results[k][u]

                if materia.ano not in ru['Matérias Legislativas']:
                    ru['Matérias Legislativas'][materia.ano] = {
                        'total': 0,
                        'paginas': 0,
                        'tramitacao': 0,
                        'ep': []
                    }

                ru['Matérias Legislativas'][materia.ano]['total'] += 1
                ru['Matérias Legislativas'][materia.ano]['tramitacao'] += materia.tramitacao_set.count()

                if materia.ano not in ru['Documentos Acessórios']:
                    ru['Documentos Acessórios'][materia.ano] = {
                        'total': 0, 'paginas': 0, 'ep': []}

                if materia.documentoacessorio_set.exists():
                    ru['Documentos Acessórios'][materia.ano]['total'] += materia.documentoacessorio_set.count()

                try:
                    ru['Matérias Legislativas'][materia.ano]['paginas'] += materia.paginas
                except:
                    ru['Matérias Legislativas'][materia.ano]['ep'].append(
                        materia.id)

                for da in materia.documentoacessorio_set.all():
                    try:
                        ru['Documentos Acessórios'][materia.ano]['paginas'] += da.paginas
                    except:
                        ru['Documentos Acessórios'][materia.ano]['ep'].append(
                            da.id)

    def run_bi_diariooficial(self, mt):
        diarios = DiarioOficial.objects.order_by('id')

        ano_cadastro = 2016
        r = {ano_cadastro: []}

        for d in diarios:
            if d.ano <= ano_cadastro:
                r[ano_cadastro].append(d)
                continue
            ano_cadastro = d.ano
            r[ano_cadastro] = [d, ]

        total = 0
        results = mt['results']
        for k, v in r.items():  # ano, lista de diarios cadastrados no ano
            if k not in results:
                results[k] = {}

            for d in v:
                # print(n)
                u = 0
                if u not in results[k]:
                    results[k][u] = {}
                    results[k][u]['Diários Oficiais'] = {}

                ru = results[k][u]

                if d.ano not in ru['Diários Oficiais']:
                    ru['Diários Oficiais'][d.ano] = {
                        'total': 0, 'paginas': 0, 'ep': []}

                ru['Diários Oficiais'][d.ano]['total'] += 1

                try:
                    ru['Diários Oficiais'][d.ano]['paginas'] += d.paginas
                except:
                    ru['Diários Oficiais'][d.ano]['ep'].append(
                        d.id)

    def run_bi_normajuridica(self, mt):
        nj = NormaJuridica.objects.order_by('id')

        ano_cadastro = 2009
        r = {ano_cadastro: []}
        for n in nj:
            if n.ano <= ano_cadastro:
                r[ano_cadastro].append(n)
                continue
            ano_cadastro = n.ano
            r[ano_cadastro] = [n, ]

        total = 0
        results = mt['results']
        for k, v in r.items():  # ano, lista de normas cadastradas no ano
            if k not in results:
                results[k] = {}

            for n in v:
                # print(n)
                u = 0
                if u not in results[k]:
                    results[k][u] = {}
                    results[k][u]['Normas Jurídicas'] = {}
                    results[k][u]['Anexos a Normas'] = {}
                    results[k][u]['Dispositivos'] = {}

                ru = results[k][u]

                if n.ano not in ru['Normas Jurídicas']:
                    ru['Normas Jurídicas'][n.ano] = {
                        'total': 0, 'paginas': 0, 'ep': []}

                if n.ano not in ru['Dispositivos']:
                    ru['Dispositivos'][n.ano] = {
                        'count': 0, }

                ru['Normas Jurídicas'][n.ano]['total'] += 1

                if n.ano not in ru['Anexos a Normas']:
                    ru['Anexos a Normas'][n.ano] = {
                        'total': 0, 'paginas': 0, 'ep': []}

                if n.texto_articulado.exists():
                    ru['Dispositivos'][n.ano]['count'] += n.texto_articulado.first().dispositivos_set.count()

                if n.anexos_set.exists():
                    ru['Anexos a Normas'][n.ano]['total'] += n.anexos_set.count()

                try:
                    ru['Normas Jurídicas'][n.ano]['paginas'] += n.paginas
                except:
                    ru['Normas Jurídicas'][n.ano]['ep'].append(
                        n.id)

                for anx in n.anexos_set.all():
                    try:
                        ru['Anexos a Normas'][n.ano]['paginas'] += anx.paginas
                    except:
                        ru['Anexos a Normas'][n.ano]['ep'].append(
                            anx.id)
