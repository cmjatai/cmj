import calendar
import datetime
import io
import json
import logging
import re
import sys
from datetime import date

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from cmj.loa import models as LoaModels
from cmj.utils import Manutencao, str2decimal

headers = {"User-Agent": "CamaraMunicipalJatai-Bot/1.0 (dde@jatai.go.leg.br)"}

urls = [
    {
        "name": "centi_getempenhos",
        "base_url": "https://api.centi.com.br",
        "endpoint": "{base_url}/portal/getempenhos/{uf}/{tenant}",
        "method": "POST",
        "type": "list",
        "format": "json",
        "params": ("ano", "covid", "dataInicio", "dataFim"),
        "page": ("size", "number"),
        "active": True,
    },
]


def consertar_json_rigoroso(texto):
    """
    Usa Expressão Regular (Regex) avançada para isolar EXATAMENTE o miolo
    das strings baseando-se nas chaves do JSON.
    """

    # PADRÃO REGEX EXPLICADO:
    # Grupo 1: ("[^"]+"\s*:\s*") -> Encontra a chave e a aspa de abertura. Ex: "historico": "
    # Grupo 2: (.*?)             -> Captura TODO o conteúdo no meio.
    # Grupo 3: ("\s*)            -> Captura a aspa de fechamento.
    # Lookahead: (?=\s*,\s*"[^"]+"\s*:|\s*,?\s*[}\]])
    # -> Garante que DEPOIS da aspa de fechamento obrigatoriamente exista uma nova chave
    #    (ex: , "nova":) OU o fim do objeto ( } ou ] ).
    padrao = re.compile(
        r'("[^"]+"\s*:\s*")' r"(.*?)" r'("\s*)' r'(?=\s*,\s*"[^"]+"\s*:|\s*,?\s*[}\]])',
        re.DOTALL,
    )

    def limpar_miolo(match):
        inicio = match.group(1)
        conteudo = match.group(2)
        fim = match.group(3)

        # 1. Troca aspas escapadas antigas (se houver) e aspas duplas indevidas por aspas simples
        conteudo = conteudo.replace('\\"', "'").replace('"', "'")

        # 2. (Opcional, mas recomendado) Remove 'Enters' e 'Tabs' literais no meio do texto
        # que também costumam causar o erro "Expecting ',' delimiter"
        conteudo = conteudo.replace("\n", " ").replace("\r", "").replace("\t", " ")

        return inicio + conteudo + fim

    # Aplica a substituição varrendo do primeiro "{" até o último "}"
    return padrao.sub(limpar_miolo, texto)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--deep", action="store_true", default=False)
        parser.add_argument("--onlychilds", action="store_true", default=False)
        parser.add_argument("--onlyoverlist", action="store_true", default=False)
        parser.add_argument("--outfile", action="store_true", default=False)
        parser.add_argument("--force", action="store_true", default=False)
        parser.add_argument("--parcial_force", action="store_true", default=False)
        parser.add_argument("--timeexec", type=int, default=30000)
        parser.add_argument(
            "--ano_inicial", type=int, default=timezone.localtime().year
        )
        parser.add_argument("--ano_final", type=int, default=timezone.localtime().year)

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)
        m = Manutencao()
        # m.desativa_auto_now()
        m.desativa_signals()

        self.force = force = options["force"]
        self.parcial_force = parcial_force = options["parcial_force"]
        self.deep = deep = options["deep"]
        self.onlychilds = onlychilds = options["onlychilds"]
        self.onlyoverlist = onlyoverlist = options["onlyoverlist"]
        outfile = options["outfile"]
        timeexec = options["timeexec"]
        self.ano_inicial = options["ano_inicial"]
        self.ano_final = options["ano_final"]
        # deep=True buscas as listas e a partir das listas, busca os registros
        # deep=False buscas apenas as listas
        # onlychilds=True ignora deep e, a partir das listas já baixadas, busca
        # os registros individuais

        if onlychilds:
            self.deep = deep = True

        if outfile:
            file_path = settings.PROJECT_DIR.child("logs").child("scrap_running.txt")
            sys.stdout = open(file_path, "r+" if file_path.exists() else "w")
            if file_path.exists():
                sys.stdout.seek(0, io.SEEK_END)

        self.time_start = timezone.localtime()

        self.ano_atual = self.time_start.year
        self.mes_atual = self.time_start.month
        self.dia_atual = self.time_start.day

        if self.ano_inicial > self.ano_final:
            raise ValueError("Ano inicial não pode ser maior que ano final.")

        print(f"START scrap: {self.time_start}")

        for url_config in urls:
            if not url_config["active"]:
                continue

            if url_config["name"] == "centi_getempenhos":
                self.centi_getempenhos(url_config)

    def centi_getempenhos(self, url_config):
        uf = "GO"
        tenant = "jatai"
        page_size = 100

        print(f"Fetching empenhos for UF={uf}, Tenant={tenant}")

        endpoint = url_config["endpoint"].format(
            base_url=url_config["base_url"], uf=uf, tenant=tenant
        )
        print(f"Constructed endpoint: {endpoint}")

        raw_data = []
        for ano in range(self.ano_final, self.ano_inicial - 1, -1):

            loa = LoaModels.Loa.objects.filter(ano=ano).first()

            if not loa:
                print(f"No Loa found for year={ano}")
                continue

            print(f"Fetching empenhos for year={ano}")
            print(f"Using endpoint: {endpoint}")
            try:
                for mes in range(12, 0, -1):
                    print(f"Fetching empenhos for month={mes}")

                    if loa.ano == ano and mes > self.mes_atual:
                        print(f"Skipping month={mes} as it is in the future")
                        continue

                    print(f"Processing empenhos for year={ano}, month={mes}")

                    primeiro_dia = date(ano, mes, 1)
                    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
                    print(f"Processing period from {primeiro_dia} to {ultimo_dia}")

                    # converter datas para 'dd/MM/yyyy'
                    primeiro_dia = primeiro_dia.strftime("%d/%m/%Y")
                    ultimo_dia = ultimo_dia.strftime("%d/%m/%Y")

                    payload = {
                        "ano": ano,
                        "covid": False,
                        "dataInicio": primeiro_dia,
                        "dataFim": ultimo_dia,
                        "page": {"number": 1, "size": page_size},
                    }
                    dados = self.fetch_empenhos(endpoint, payload)
                    if dados:
                        raw_data.extend(dados)

                    TotalRegistros = dados[0].get("TotalRegistros")
                    TotalPaginas = TotalRegistros // page_size + (
                        1 if TotalRegistros % page_size > 0 else 0
                    )

                    for page_number in range(2, TotalPaginas + 1):
                        payload["page"]["number"] = page_number
                        dados = self.fetch_empenhos(endpoint, payload)
                        if dados:
                            raw_data.extend(dados)
                    # if mes == 9:
                    break
            except Exception as e:
                print(f"Erro ao processar empenhos para ano={ano}: {e}")
            break
        for item_centi in raw_data:
            self.update_or_create_empenho(item_centi)
            # print(item)

    def update_or_create_empenho(self, item_centi):
        data = item_centi.get("Data", None)
        if not data:
            return

        data = datetime.datetime.strptime(data, "%d/%m/%Y").date()

        Id = item_centi.get("Id", None)
        Numero = item_centi.get("Numero", None)
        Sequencial = item_centi.get("Sequencial", None)
        Fornecedor = item_centi.get("Fornecedor", None)
        ValorEmpenhado = item_centi.get("ValorEmpenhado", 0)
        ValorAnulacao = item_centi.get("ValorAnulacao", 0)
        ValorLiquidado = item_centi.get("ValorLiquidado", 0)
        SaldoPagar = item_centi.get("SaldoPagar", 0)
        ValorPago = item_centi.get("ValorPago", 0)
        FonteRecurso = item_centi.get("FonteRecurso", None)
        DestinacaoRecurso = item_centi.get("DestinacaoRecurso", None)
        OrgaoGestor = item_centi.get("OrgaoGestor", None)
        Unidade = item_centi.get("UnidadeOrcamentaria", None)
        Funcao = item_centi.get("Funcao", None)
        SubFuncao = item_centi.get("SubFuncao", None)
        Programa = item_centi.get("Programa", None)
        Acao = item_centi.get("Acao", None)
        CpfCnpjCredor = item_centi.get("CpfCnpjCredor", None)
        LicitacaoModalidade = item_centi.get("LicitacaoModalidade", None)
        IdLicitacaoDispensaAdesao = item_centi.get("IdLicitacaoDispensaAdesao", None)
        Historico = item_centi.get("Historico", None)
        Elemento = item_centi.get("Elemento", None)
        SubElemento = item_centi.get("SubElemento", None)

        ValorEmpenhado = str2decimal(ValorEmpenhado)
        ValorAnulacao = str2decimal(ValorAnulacao)
        ValorLiquidado = str2decimal(ValorLiquidado)
        ValorPago = str2decimal(ValorPago)
        SaldoPagar = str2decimal(SaldoPagar)

        map_values = {
            "orgao": [OrgaoGestor, slugify(OrgaoGestor), LoaModels.Orgao],
            "unidade": [Unidade, slugify(Unidade), LoaModels.UnidadeOrcamentaria],
            "funcao": [Funcao, slugify(Funcao), LoaModels.Funcao],
            "subfuncao": [SubFuncao, slugify(SubFuncao), LoaModels.SubFuncao],
            "programa": [Programa, slugify(Programa), LoaModels.Programa],
            "acao": [Acao, slugify(Acao), LoaModels.Acao],
        }

        loa = LoaModels.Loa.objects.get(ano=data.year)

        for key, [value, slug, model] in map_values.items():
            params = {
                "loa__ano": data.year,
                "metadata__scrap__key_especificacao": slug,
            }
            if key == "unidade":
                params["orgao__metadata__scrap__key_especificacao"] = map_values[
                    "orgao"
                ][1]
            elif key == "subfuncao":
                params["funcao__metadata__scrap__key_especificacao"] = map_values[
                    "funcao"
                ][1]

            obj = model.objects.filter(**params).first()
            if not obj:
                obj = model()
                obj.loa = loa
                obj.especificacao = value
                if key == "unidade":
                    obj.orgao = map_values["orgao"][
                        3
                    ]  # Assign the 'orgao' object to the 'unidade' if key is 'unidade'
                if key == "subfuncao":
                    obj.funcao = map_values["funcao"][
                        3
                    ]  # Assign the 'funcao' object to the 'subfuncao' if key is 'subfuncao'
                obj.save()

            map_values[key] = [value, slug, model, obj]

        elemento = Elemento.split(" - ")
        natureza = LoaModels.Natureza.objects.filter(
            loa__ano=data.year,
            codigo__iexact=elemento[0],
            # especificacao__iexact=elemento[1],
        ).first()
        if not natureza:
            natureza = LoaModels.Natureza()
            natureza.loa_id = loa.id
            natureza.especificacao = elemento[1]
            natureza.codigo = elemento[0]
            natureza.save()

        fonteRecurso = FonteRecurso.split(" - ", 1)
        fonteRecursoCodigo = "".join(filter(str.isdigit, fonteRecurso[0]))
        especFonteRecurso = fonteRecurso[1].strip()
        fonteRecurso = LoaModels.Fonte.objects.filter(
            loa__ano=data.year, codigo__iexact=fonteRecursoCodigo
        ).first()
        if not fonteRecurso:
            fonteRecurso = LoaModels.Fonte()
            fonteRecurso.loa_id = loa.id
            fonteRecurso.especificacao = especFonteRecurso
            fonteRecurso.codigo = fonteRecursoCodigo
            fonteRecurso.save()

        destinacaoRecurso = DestinacaoRecurso.split(" - ", 1)
        destinacaoRecursoCodigo = "".join(filter(str.isdigit, destinacaoRecurso[0]))
        especDestinacaoRecurso = destinacaoRecurso[1].strip()

        destinacaoRecursoCodigo = f"{fonteRecursoCodigo}.{destinacaoRecursoCodigo}"
        destinacaoRecurso = LoaModels.Fonte.objects.filter(
            loa__ano=data.year, codigo__iexact=destinacaoRecursoCodigo
        ).first()
        if not destinacaoRecurso:
            destinacaoRecurso = LoaModels.Fonte()
            destinacaoRecurso.loa_id = loa.id
            destinacaoRecurso.especificacao = especDestinacaoRecurso
            destinacaoRecurso.codigo = destinacaoRecursoCodigo
            destinacaoRecurso.save()

        empenho = LoaModels.Empenho.objects.filter(
            codigo=Sequencial or Numero or Id
        ).first()
        if not empenho:
            empenho = LoaModels.Empenho()
            empenho.id = Sequencial or Numero or Id
            empenho.codigo = Sequencial or Numero or Id

        md = empenho.metadata or {}
        md["scrap"] = md.get("scrap", {})
        empenho.metadata = md
        md["scrap"]["values"] = {
            "Número": Numero,
            "CpfCnpjCredor": CpfCnpjCredor,
            "Fornecedor": Fornecedor,
            "Histórico": Historico,
            "LicitacaoModalidade": LicitacaoModalidade,
            "IdLicitacaoDispensaAdesao": IdLicitacaoDispensaAdesao,
            "Orgão": str(map_values["orgao"][3]),
            "Unidade": str(map_values["unidade"][3]),
            "Função": str(map_values["funcao"][3]),
            "Sub-Função": str(map_values["subfuncao"][3]),
            "Programa": str(map_values["programa"][3]),
            "Ação": str(map_values["acao"][3]),
            "Natureza": str(natureza),
            "Sub-Elemento": SubElemento,
            "Fonte Recurso": str(fonteRecurso),
            "Destinação Recurso": str(destinacaoRecurso),
        }

        empenho.cpfcnpj = CpfCnpjCredor
        if len(CpfCnpjCredor) == 14:
            empenho.cpfcnpj = f"{CpfCnpjCredor[:3]}.***.***-{CpfCnpjCredor[12:]}"
            md["scrap"]["values"]["CpfCnpjCredor"] = empenho.cpfcnpj

        empenho.data = data
        empenho.nome = Fornecedor
        empenho.processo = ""

        empenho.valor_empenhado = ValorEmpenhado
        empenho.valor_anulado = ValorAnulacao
        empenho.valor_liquidado = ValorLiquidado
        empenho.valor_pago_bruto = ValorPago

        empenho.historico = Historico
        empenho.modalidade = LicitacaoModalidade
        empenho.numero_licitacao = IdLicitacaoDispensaAdesao

        empenho.orgao = map_values["orgao"][3]
        empenho.unidade = map_values["unidade"][3]
        empenho.funcao = map_values["funcao"][3]
        empenho.subfuncao = map_values["subfuncao"][3]
        empenho.programa = map_values["programa"][3]
        empenho.acao = map_values["acao"][3]

        empenho.natureza = natureza
        empenho.fonte = destinacaoRecurso

        empenho.save()

    def fetch_empenhos(self, endpoint, payload):
        response_text = None
        try:
            print(f"Buscando dados em: {endpoint}...")

            # Adicionamos o argumento headers=headers aqui
            headers = {"Content-Type": "application/json"}
            response = requests.post(endpoint, json=payload, headers=headers)

            # Dispara uma exceção se o status code for um erro
            response.raise_for_status()
            response_text = response.text

        except requests.exceptions.HTTPError as errh:
            print(f"Erro da API (HTTP Error): {errh}")
            print(f"Detalhes do erro: {response.text}")
        except requests.exceptions.RequestException as err:
            print(f"Erro de conexão ou requisição: {err}")
        except Exception as err:
            print(f"Erro inesperado: {err}")

        if not response_text:
            return []

        try:
            dados = json.loads(response_text)
            print("Sucesso!")
        except json.JSONDecodeError as e:
            try:
                texto_limpo = consertar_json_rigoroso(response_text)
                dados = json.loads(texto_limpo)
                print("Sucesso após conserto!")
            except json.JSONDecodeError as e2:
                print(f"Falha ao tentar consertar o JSON: {e2}")
                dados = []

        return dados
