import logging

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.db.models.signals import post_delete, post_save
from pdfrw.pdfreader import PdfReader

from cmj.core.models import Bi
from cmj.diarios.models import DiarioOficial
from cmj.sigad.models import VersaoDeMidia
from sapl.materia.models import MateriaLegislativa
from sapl.norma.models import NormaJuridica, AnexoNormaJuridica
from sapl.protocoloadm.models import DocumentoAdministrativo,\
    DocumentoAcessorioAdministrativo


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
        models = [
            {
                'model': MateriaLegislativa,
                'file_field': 'texto_original',
                'hook': 'run_bi_materias_legislativas',
                'results': {},
            },
            {
                'model': NormaJuridica,
                'file_field': 'texto_integral',
                'hook': ''
            },
            {
                'model': AnexoNormaJuridica,
                'file_field': 'anexo_arquivo',
                'hook': ''
            },
            {
                'model': DocumentoAdministrativo,
                'file_field': 'texto_integral',
                'hook': ''
            },
            {
                'model': DocumentoAcessorioAdministrativo,
                'file_field': 'arquivo',
                'hook': ''
            },
            {
                'model': DiarioOficial,
                'file_field': 'arquivo',
                'hook': ''
            },
            {
                'model': VersaoDeMidia,
                'file_field': 'file',
                'hook': ''
            },
        ]

        for mt in models:  # mt = metadata
            if not mt['hook']:
                continue
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
                results[k]['tramitacao'] = 0

            for materia in v:

                if materia.tramitacao_set.exists():
                    results[k]['tramitacao'] += materia.tramitacao_set.count()

                u = materia.user_id if materia.ano == 2020 else (
                    materia.user_id if materia.user_id else 0)
                if u not in results[k]:
                    results[k][u] = {}
                    results[k][u]['materialegislativa'] = {}
                    results[k][u]['documentoacessorio'] = {}

                ru = results[k][u]

                if materia.ano not in ru['materialegislativa']:
                    ru['materialegislativa'][materia.ano] = {
                        'total': 0, 'paginas': 0, 'ep': []}
                ru['materialegislativa'][materia.ano]['total'] += 1

                if materia.ano not in ru['documentoacessorio']:
                    ru['documentoacessorio'][materia.ano] = {
                        'total': 0, 'paginas': 0, 'ep': []}

                if materia.documentoacessorio_set.exists():
                    ru['documentoacessorio'][materia.ano]['total'] += materia.documentoacessorio_set.count()

                try:
                    ru['materialegislativa'][materia.ano]['paginas'] += materia.paginas
                except:
                    ru['materialegislativa'][materia.ano]['ep'].append(
                        materia.id)

                for da in materia.documentoacessorio_set.all():
                    try:
                        ru['documentoacessorio'][materia.ano]['paginas'] += da.paginas
                    except:
                        ru['documentoacessorio'][materia.ano]['ep'].append(
                            da.id)
