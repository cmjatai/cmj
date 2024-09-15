from copy import deepcopy
import csv
from io import StringIO
import logging
import sys
from time import sleep

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
import requests

from cmj.loa import models
from cmj.loa.models import ScrapRecord
from cmj.utils import Manutencao


urls = [
    {
        'name': 'despesa_paga_list_exportacao',
        'url': 'http://prefeituradejatai.sigepnet.com.br/transparencia/exportacao/'
        'despesa_paga.php?extensao=CSV&orgao={orgao}&ano={ano}&mes={mes}&fornecedor=&cpfcnpj=&acao=true',
        'type': 'list',
        'format': 'csv',
        'params': ('orgao', 'mes', 'ano'),
        'childs': [
            {
                'name': 'despesa_paga_detalhes_exportacao',
                'url': 'http://prefeituradejatai.sigepnet.com.br/transparencia/exportacao/'
                'depesa_paga_detalhes.php?extensao=CSV&codigo={codigo}',
                'type': 'detail',
                'format': 'csv',
                'params': ('codigo', ),
            },
            {
                'name': 'despesa_paga_detalhes',
                'url': 'http://prefeituradejatai.sigepnet.com.br/transparencia/'
                'despesa_paga_detalhes.php?codigo={codigo}',
                'type': 'detail',
                'format': 'html',
                'params': ('codigo', ),
            },
        ]
    },
    {
        'name': 'receita_list_exportacao',
        'url': 'http://prefeituradejatai.sigepnet.com.br/transparencia/exportacao/'
        'receitas.php?extensao=CSV&orgao={orgao}&ano={ano}&mes={mes}&elementoreceita=&categoria=&origem=&especie=&acao=true',
        'type': 'list',
        'params': ('orgao', 'mes', 'ano'),
        'format': 'csv',
        'childs': [
            {
                'name': 'receita_detail_exportacao',
                'url': 'http://prefeituradejatai.sigepnet.com.br/transparencia/exportacao/'
                'receitas_detalhes.php?extensao=CSV&codigo={codigo}&orgao={orgao}&ano={ano}&mes={mes}',
                'type': 'list',
                'format': 'csv',
                'params': ('codigo', 'orgao', 'mes', 'ano')
            },
            {
                'name': 'receita_detail',
                'url': 'http://prefeituradejatai.sigepnet.com.br/transparencia/'
                'receitas_detalhes.php?codigo={codigo}&orgao={orgao}&ano={ano}&mes={mes}',
                'type': 'list',
                'format': 'html',
                'params': ('codigo', 'orgao', 'mes', 'ano')
            },
        ]
    }
]


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        m = Manutencao()
        # m.desativa_auto_now()
        m.desativa_signals()

        file_path = settings.PROJECT_DIR.child(
            'logs').child('scrap_running.txt')
        sys.stdout = open(file_path, "w")
        self.time_start = timezone.localtime()

        self.ano_atual = self.time_start.year
        self.mes_atual = self.time_start.month

        orgaos = models.Orgao.objects.order_by('-codigo', '-loa__ano')
        for url_dict in urls:
            orgao_atual = None
            interromper_orgao = False
            for orgao in orgaos:
                if orgao.loa.ano > self.ano_atual or orgao.codigo == '01':
                    continue

                if interromper_orgao and orgao.codigo == orgao_atual.codigo:
                    continue
                interromper_orgao = False
                orgao_atual = orgao

                for mes in range(12, 0, -1):
                    if orgao.loa.ano == self.ano_atual and mes > self.mes_atual:
                        continue

                    params = {
                        'orgao': orgao.codigo,
                        'ano': orgao.loa.ano,
                        'mes': f'{mes:>02}'
                    }

                    try:
                        print(
                            f'START: {timezone.localtime()}, Órgão: {orgao}, Ano: {orgao.loa.ano}, Mês: {mes}, Url_dict: {url_dict["name"]}')
                        interromper_orgao = self.scrap_node(
                            url_dict, params=params)
                        print('END: ok')
                        sys.stdout.flush()
                    except:
                        print('END: error')

                    if interromper_orgao:
                        break

    def scrap_node(self, url_dict, params={}, item_list=[], parent=None):
        sleep(1)
        try:
            url = url_dict['url'].format(**params)
        except:
            url = url_dict['url'].format(codigo=params['codigo'])

        try:
            get = requests.get(url)
            print(f'... url: {url}')
            sys.stdout.flush()
        except:
            print(f'ERRO get: {url}')
            return True

        content = get.content

        scrap = ScrapRecord.objects.filter(url=url).first()

        childs = url_dict.get('childs', [])
        if scrap:

            if url_dict['format'] == 'html':
                if scrap.content.tobytes() == content:
                    return True
            elif url_dict['format'] == 'csv':
                is_equals = self.compare_bytes_csv(
                    scrap.content.tobytes(), content)
                if is_equals:
                    return True
            scrap.content = content
            scrap.save()

            if childs:
                self.scrap_run_childs(scrap, childs, params)
            return False

        scrap = ScrapRecord()
        scrap.url = url
        scrap.orgao = params['orgao']
        scrap.codigo = params.get('codigo', '')
        scrap.ano = params['ano']
        scrap.mes = params['mes']
        scrap.metadata = {
            'url_dict': url_dict,
            'item_list': item_list
        }
        scrap.parent = parent
        scrap.content = content
        scrap.save()

        if childs:
            self.scrap_run_childs(scrap, childs, params)
        return False

    def scrap_run_childs(self, scrap, url_childs, params):
        content = scrap.content.decode('utf-8-sig')
        file = StringIO(content)
        csv_data = csv.reader(file, delimiter=";")

        idx_codigo = -1
        for idx, row in enumerate(csv_data):

            if not idx:
                try:
                    idx_codigo = row.index("CÓDIGO")
                except:
                    try:
                        idx_codigo = row.index("RECEITA")
                    except:
                        return
                continue

            for url_dict in url_childs:
                pms = deepcopy(params)
                pms['codigo'] = row[idx_codigo]

                self.scrap_node(url_dict, params=pms,
                                item_list=row, parent=scrap)

    def compare_bytes_csv(self, c1, c2):
        str1_csv = c1.decode('utf-8-sig')
        str2_csv = c2.decode('utf-8-sig')
        f1 = StringIO(str1_csv)
        f2 = StringIO(str2_csv)
        csv1 = list(csv.reader(f1, delimiter=';'))
        csv2 = list(csv.reader(f2, delimiter=';'))
        csv1 = sorted(csv1, key=lambda i: i)
        csv2 = sorted(csv2, key=lambda i: i)

        return csv1 == csv2
