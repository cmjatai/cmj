from copy import deepcopy
from io import StringIO
from time import sleep
import csv
import io
import json
import logging
import sys

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
        'url': 'http://{subdomain}.sigepnet.com.br/transparencia/exportacao/'
        'despesa_paga.php?extensao=CSV&orgao={orgao}&ano={ano}&mes={mes}&fornecedor=&cpfcnpj=&acao=true',
        'type': 'list',
        'format': 'csv',
        'params': ('orgao', 'mes', 'ano'),
        'subdomain': ('prefeituradejatai', 'camaradejatai'),
        'childs': [
            {
                'name': 'despesa_paga_detalhes_exportacao',
                'url': 'http://{subdomain}.sigepnet.com.br/transparencia/exportacao/'
                'depesa_paga_detalhes.php?extensao=CSV&codigo={codigo}',
                'type': 'detail',
                'format': 'csv',
                'params': ('codigo', ),
                'subdomain': ('prefeituradejatai', 'camaradejatai'),
            },
            {
                'name': 'despesa_paga_detalhes',
                'url': 'http://{subdomain}.sigepnet.com.br/transparencia/'
                'despesa_paga_detalhes.php?codigo={codigo}',
                'type': 'detail',
                'format': 'html',
                'params': ('codigo', ),
                'subdomain': ('prefeituradejatai', 'camaradejatai'),
            },
        ]
    },
    {
        'name': 'receita_list_exportacao',
        'url': 'http://{subdomain}.sigepnet.com.br/transparencia/exportacao/'
        'receitas.php?extensao=CSV&orgao={orgao}&ano={ano}&mes={mes}&elementoreceita=&categoria=&origem=&especie=&acao=true',
        'type': 'list',
        'params': ('orgao', 'mes', 'ano'),
        'format': 'csv',
        'subdomain': ('prefeituradejatai', ),
        'childs': [
            {
                'name': 'receita_detail_exportacao',
                'url': 'http://{subdomain}.sigepnet.com.br/transparencia/exportacao/'
                'receitas_detalhes.php?extensao=CSV&codigo={codigo}&orgao={orgao}&ano={ano}&mes={mes}',
                'type': 'list',
                'format': 'csv',
                'params': ('codigo', 'orgao', 'mes', 'ano'),
                'subdomain': ('prefeituradejatai', ),
            },
            {
                'name': 'receita_detail',
                'url': 'http://{subdomain}.sigepnet.com.br/transparencia/'
                'receitas_detalhes.php?codigo={codigo}&orgao={orgao}&ano={ano}&mes={mes}',
                'type': 'list',
                'format': 'html',
                'params': ('codigo', 'orgao', 'mes', 'ano'),
                'subdomain': ('prefeituradejatai', ),
            },
        ]
    },
    {
        'name': 'transferencia_recursos_list_exportacao',
        'url': 'http://{subdomain}.sigepnet.com.br/transparencia/exportacao/'
        'transferencia_de_recursos.php?extensao=CSV&orgao={orgao}&ano={ano}&mes={mes}&receita_despesa=&acao=true',
        'type': 'list',
        'params': ('orgao', 'mes', 'ano'),
        'format': 'csv',
        'subdomain': ('camaradejatai', ),
    }
]


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--deep', action='store_true', default=False)
        parser.add_argument('--onlychilds', action='store_true', default=False)
        parser.add_argument('--outfile', action='store_true', default=False)
        parser.add_argument('--force', action='store_true', default=False)
        parser.add_argument('--timeexec', type=int, default=80000)

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        m = Manutencao()
        # m.desativa_auto_now()
        m.desativa_signals()

        self.force = force = options['force']
        self.deep = deep = options['deep']
        self.onlychilds = onlychilds = options['onlychilds']
        outfile = options['outfile']
        timeexec = options['timeexec']

        # deep=True buscas as listas e a partir das listas, busca os registros
        # deep=False buscas apenas as listas
        # onlychilds=True ignora deep e, a partir das listas já baixadas, busca
        # os registros individuais

        if onlychilds:
            self.deep = deep = True

        if outfile:
            file_path = settings.PROJECT_DIR.child(
                'logs').child('scrap_running.txt')
            sys.stdout = open(file_path, 'r+' if file_path.exists() else 'w')
            if file_path.exists():
                sys.stdout.seek(0, io.SEEK_END)

        self.time_start = timezone.localtime()

        print(f'START scrap: {self.time_start}')
        sys.stdout.flush()

        self.ano_atual = self.time_start.year
        self.mes_atual = self.time_start.month

        order_by = (
            '-loa__ano', 'codigo') if onlychilds else ('codigo', '-loa__ano')
        #order_by = ('-loa__ano', 'codigo')

        subdomains = [
            {
                'subdomain': 'camaradejatai',
                'orgaos': models.Orgao.objects.filter(codigo='01').order_by(*order_by),
            },
            {
                'subdomain': 'prefeituradejatai',
                'orgaos': models.Orgao.objects.exclude(codigo='01').order_by(*order_by),
            },
        ]

        # ScrapRecord.objects.all().delete()
        urls.reverse()

        # 558404
        # for scrap in ScrapRecord.objects.filter(codigo='477275').order_by('-codigo'):
        #    scrap.update_data_models()
        # return

        for sd in subdomains:
            for url_dict in urls:

                if sd['subdomain'] not in url_dict['subdomain']:
                    continue

                udj = json.dumps(url_dict)
                udj = udj.replace('{subdomain}', sd['subdomain'])
                ud = json.loads(udj)

                orgao_atual = None
                interromper_orgao = False
                for orgao in sd['orgaos']:
                    if orgao.loa.ano > self.ano_atual:
                        continue

                    if interromper_orgao and orgao.codigo == orgao_atual.codigo:
                        continue
                    interromper_orgao = False
                    orgao_atual = orgao

                    for mes in range(12, 0, -1):

                        if (timezone.localtime() - self.time_start).seconds > timeexec:
                            return

                        if orgao.loa.ano == self.ano_atual and mes > self.mes_atual:
                            continue

                        params = {
                            'orgao': orgao.codigo,
                            'ano': orgao.loa.ano,
                            'mes': f'{mes:>02}'
                        }

                        try:
                            self.hora_atual = timezone.localtime().hour
                            self.weekday = timezone.localtime().weekday()
                            print(
                                f'START: {timezone.localtime()}, Órgão: {orgao}, Ano: {orgao.loa.ano}, Mês: {mes}, Url_dict: {url_dict["name"]}')
                            interromper_orgao = self.scrap_node(
                                ud, params=params, deep=deep)
                            print('END: ok')
                            sys.stdout.flush()
                        except Exception as e:
                            print('END: error', e)

                        if interromper_orgao:
                            break

    def scrap_node(self, url_dict, params={}, item_list=[], parent=None, deep=True):

        def get_content(url):

            # if 6 < self.hora_atual < 22 and self.weekday < 5:
            #    sleep(10)

            try:
                get = requests.get(url)
                print(f'... url: {url}')
                sys.stdout.flush()
            except:
                print(f'ERRO get: {url}')
                return False
            content = get.content
            return content

        try:
            url = url_dict['url'].format(**params)
        except:
            url = url_dict['url'].format(codigo=params['codigo'])

        scrap = ScrapRecord.objects.filter(url=url).first()
        content_scrap = b''
        content_download = b''

        if not scrap or not scrap.content:
            content_download = get_content(url)
        elif self.force:
            if self.onlychilds and parent:
                content_download = get_content(url)
            elif not self.onlychilds:
                content_download = get_content(url)
        else:
            if not self.onlychilds and not parent:
                content_download = get_content(url)

        if isinstance(content_download, bool):
            return True  # para o scrap para o órgão atual

        childs = url_dict.get('childs', [])

        if scrap:

            if not self.force:
                content_scrap = scrap.content.tobytes()
                if scrap.metadata['item_list'] != item_list:
                    scrap.metadata['item_list'] = item_list
                    scrap.save(update_fields=('metadata',))
                scrap.update_data_models()

            if url_dict['format'] == 'html':
                if content_scrap == content_download:
                    return True
            elif url_dict['format'] == 'csv':
                is_equals = self.compare_bytes_csv(
                    content_scrap, content_download)
                if is_equals and not self.onlychilds:
                    return True

            if not self.onlychilds or content_download:
                scrap.content = content_download
                scrap.metadata['item_list'] = item_list
                scrap.save(update_fields=('metadata', 'content'))
                scrap.update_data_models()

            if childs and deep:
                self.scrap_run_childs(scrap, childs, params, deep)
            return False

        scrap = ScrapRecord()
        scrap.url = url
        scrap.orgao = params['orgao']
        scrap.codigo = params.get('codigo', '')
        scrap.ano = int(params['ano'])
        scrap.mes = int(params['mes'])
        scrap.metadata = {
            'url_dict': url_dict,
            'item_list': item_list
        }
        scrap.parent = parent
        scrap.content = content_download
        scrap.save()

        scrap.update_data_models()

        if childs and deep:
            self.scrap_run_childs(scrap, childs, params, deep)
        return False

    def scrap_run_childs(self, scrap, url_childs, params, deep):
        content = scrap.content
        if isinstance(content, memoryview):
            content = content.tobytes()

        content = content.decode('utf-8-sig')
        file = StringIO(content)
        csv_data = csv.reader(file, delimiter=";")

        idx_codigo = -1
        lista = list(enumerate(csv_data))
        if not lista:
            return
        rows = lista[1:-1]
        rows = sorted(rows, key=lambda x: x[1][0])
        rows.reverse()

        try:
            idx_codigo = lista[0][1].index("CÓDIGO")
        except:
            try:
                idx_codigo = lista[0][1].index("RECEITA")
            except:
                return

        for idx, row in rows:

            for url_dict in url_childs:
                pms = deepcopy(params)
                pms['codigo'] = row[idx_codigo]

                self.scrap_node(url_dict, params=pms,
                                item_list=row, parent=scrap, deep=deep)

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
