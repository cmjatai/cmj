import calendar
import datetime
import hashlib
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

DEFAULT_HEADERS = {"User-Agent": "CamaraMunicipalJatai-Bot/1.0 (dde@jatai.go.leg.br)"}

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


def sanitize_json_content(texto):
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

    def sanitize_content(match):
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
    return padrao.sub(sanitize_content, texto)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--outfile", action="store_true", default=False)
        parser.add_argument("--force", action="store_true", default=False)
        parser.add_argument("--stopinpage", action="store_true", default=False)
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
        self.stopinpage = stopinpage = options["stopinpage"]
        self.ano_inicial = options["ano_inicial"]
        self.ano_final = options["ano_final"]
        outfile = options["outfile"]

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

        print("")
        print("=" * 70)
        print(f"[scrap_centi] INÍCIO em {self.time_start:%d/%m/%Y %H:%M:%S}")
        print(
            f"[scrap_centi] Período solicitado: {self.ano_inicial} a {self.ano_final} "
            f"| force={self.force} | stopinpage={self.stopinpage}"
        )
        print("=" * 70)

        for url_config in urls:
            if not url_config["active"]:
                continue

            if url_config["name"] == "centi_getempenhos":
                self.centi_getempenhos(url_config)

        time_end = timezone.localtime()
        print("=" * 70)
        print(
            f"[scrap_centi] FIM em {time_end:%d/%m/%Y %H:%M:%S} "
            f"(duração: {time_end - self.time_start})"
        )
        print("=" * 70)

    def centi_getempenhos(self, url_config):
        uf = "go"
        tenant = "jatai"
        page_size = 100

        print(f"[scrap_centi] Fetching empenhos for UF={uf}, Tenant={tenant}")

        endpoint = url_config["endpoint"].format(
            base_url=url_config["base_url"], uf=uf, tenant=tenant
        )
        print(f"[scrap_centi] Endpoint: {endpoint}")

        raw_data_global = []
        for ano in range(self.ano_final, self.ano_inicial - 1, -1):

            loa = LoaModels.Loa.objects.filter(ano=ano).first()

            if not loa:
                print(
                    f"[scrap_centi] [{ano}] LOA não cadastrada para o ano — ano ignorado."
                )
                continue

            print(f"\n[scrap_centi] === Ano {ano}: iniciando varredura mensal ===")

            for mes in range(12, 0, -1):
                # resetado a cada mês para não herdar valor de iteração anterior
                # em caso de exceção (evita interrupção indevida do loop de meses)
                updated_count = 0
                try:
                    if loa.ano == ano and mes > self.mes_atual:
                        print(f"[scrap_centi] [{ano}-{mes:02d}] mês futuro — ignorado.")
                        continue

                    primeiro_dia = date(ano, mes, 1)
                    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

                    # converter datas para 'dd/MM/yyyy'
                    primeiro_dia_str = primeiro_dia.strftime("%d/%m/%Y")
                    ultimo_dia_str = ultimo_dia.strftime("%d/%m/%Y")

                    print(
                        f"[scrap_centi] [{ano}-{mes:02d}] buscando empenhos de "
                        f"{primeiro_dia_str} a {ultimo_dia_str}..."
                    )

                    raw_data = []
                    payload = {
                        "ano": ano,
                        "covid": False,
                        "dataInicio": primeiro_dia_str,
                        "dataFim": ultimo_dia_str,
                        "page": {"number": 1, "size": page_size},
                    }

                    dados = self.fetch_empenhos(endpoint, payload)
                    if not dados:
                        print(
                            f"[scrap_centi] [{ano}-{mes:02d}] nenhum registro retornado "
                            f"pela API — mês ignorado."
                        )
                        continue

                    raw_data.extend(dados)

                    # TotalRegistros pode vir ausente/None da API — default evita TypeError
                    TotalRegistros = dados[0].get("TotalRegistros") or 0
                    TotalPaginas = TotalRegistros // page_size + (
                        1 if TotalRegistros % page_size > 0 else 0
                    )
                    print(
                        f"[scrap_centi] [{ano}-{mes:02d}] {TotalRegistros} registro(s) "
                        f"em {TotalPaginas} página(s)."
                    )

                    def processa_dados(_dados):
                        """Processa os itens isoladamente: falha em 1 empenho não aborta os demais."""
                        sucesso = 0
                        for item_centi in _dados:
                            codigo_item = (
                                item_centi.get("Sequencial")
                                or item_centi.get("Numero")
                                or item_centi.get("Id")
                            )
                            try:
                                empenho, updated_or_created = (
                                    self.update_or_create_empenho(item_centi)
                                )
                            except Exception as e:
                                print(
                                    f"[scrap_centi] [{ano}-{mes:02d}] ERRO ao gravar "
                                    f"empenho código={codigo_item}: {e}"
                                )
                                self.logger.error(
                                    f"Erro ao processar empenho ano={ano} mes={mes} "
                                    f"codigo={codigo_item}: {e}",
                                    exc_info=True,
                                )
                                continue

                            if not empenho:
                                continue

                            # se None, então o md5 de item_centi não mudou
                            if updated_or_created is not None:
                                sucesso += 1

                        return sucesso

                    # acumula alterações de todas as páginas; antes era reatribuído
                    # para 0 após o loop de páginas, mascarando o resultado real
                    # quando --stopinpage estava ativo (bug: sempre interrompia o
                    # mês seguinte por crer que não houve alterações)
                    mes_updated_count = 0

                    if not self.force and self.stopinpage:
                        mes_updated_count += processa_dados(dados)
                        print(
                            f"[scrap_centi] [{ano}-{mes:02d}] página 1/{TotalPaginas}: "
                            f"{mes_updated_count} alteração(ões)."
                        )

                    for page_number in range(2, TotalPaginas + 1):
                        payload["page"]["number"] = page_number
                        print(
                            f"[scrap_centi] [{ano}-{mes:02d}] buscando página "
                            f"{page_number}/{TotalPaginas}..."
                        )
                        dados_pagina = self.fetch_empenhos(endpoint, payload)
                        if dados_pagina:
                            raw_data.extend(dados_pagina)

                        if not self.force and self.stopinpage:
                            pagina_updated_count = processa_dados(dados_pagina)
                            mes_updated_count += pagina_updated_count
                            print(
                                f"[scrap_centi] [{ano}-{mes:02d}] página "
                                f"{page_number}/{TotalPaginas}: "
                                f"{pagina_updated_count} alteração(ões)."
                            )
                            if not pagina_updated_count:
                                print(
                                    f"[scrap_centi] [{ano}-{mes:02d}] sem alterações "
                                    f"na página {page_number} — paginação do mês "
                                    f"interrompida."
                                )
                                break

                        self.stdout.flush()

                    raw_data_global.extend(raw_data)

                    if not self.force and not self.stopinpage:
                        mes_updated_count = processa_dados(raw_data)

                    updated_count = mes_updated_count

                    print(
                        f"[scrap_centi] [{ano}-{mes:02d}] mês concluído: "
                        f"{updated_count} empenho(s) novo(s)/atualizado(s) de "
                        f"{len(raw_data)} recebido(s)."
                    )

                    if not self.force and not updated_count:
                        # se nenhuma modificação nos empenhos então interrompe o loop de mês
                        print(
                            f"[scrap_centi] [{ano}-{mes:02d}] sem novidades neste "
                            f"mês — varredura do ano {ano} interrompida."
                        )
                        break

                except Exception as e:
                    print(
                        f"[scrap_centi] [{ano}-{mes:02d}] ERRO inesperado ao "
                        f"processar o mês: {e}"
                    )
                    self.logger.error(
                        f"Erro ao processar empenhos para ano={ano} mes={mes}: {e}",
                        exc_info=True,
                    )
                    continue

            print(f"[scrap_centi] === Ano {ano}: varredura finalizada ===")

    @staticmethod
    def _split_codigo_especificacao(valor, sep=" - "):
        """Separa 'codigo - especificação' sem quebrar quando o padrão não é seguido."""
        if not valor:
            return "", ""
        partes = valor.split(sep, 1)
        codigo = partes[0].strip()
        especificacao = partes[1].strip() if len(partes) > 1 else ""
        return codigo, especificacao

    def update_or_create_empenho(self, item_centi):
        dataItem = item_centi.get("Data", None)
        if not dataItem:
            return None, None

        data = datetime.datetime.strptime(dataItem, "%d/%m/%Y").date()

        Id = item_centi.get("Id", None)
        Numero = item_centi.get("Numero", None)
        Sequencial = item_centi.get("Sequencial", None)

        empenho = LoaModels.Empenho.objects.filter(
            codigo=Sequencial or Numero or Id
        ).first()
        created = False
        if not empenho:
            empenho = LoaModels.Empenho()
            empenho.id = Sequencial or Numero or Id
            empenho.codigo = Sequencial or Numero or Id
            created = True

        str_item_centi = str(sorted(item_centi.items()))
        new_md5 = hashlib.md5()
        new_md5.update(str_item_centi.encode("utf-8"))
        new_md5 = new_md5.hexdigest()

        md = empenho.metadata or {}
        md["scrap"] = md.get("scrap", {})
        md5_old = md["scrap"].get("md5", "")

        if md5_old == new_md5:
            return (
                empenho,
                None,
            )  # retorna terceiro estado indicando que não houve alterações, testado via hash

        md["scrap"]["md5"] = new_md5

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
        CpfCnpjCredor = item_centi.get("CpfCnpjCredor", None) or ""
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

        elemento_codigo, elemento_especificacao = self._split_codigo_especificacao(
            Elemento
        )
        natureza = LoaModels.Natureza.objects.filter(
            loa__ano=data.year,
            codigo__iexact=elemento_codigo,
        ).first()
        if not natureza:
            natureza = LoaModels.Natureza()
            natureza.loa_id = loa.id
            natureza.especificacao = elemento_especificacao
            natureza.codigo = elemento_codigo
            natureza.save()

        fonteRecurso_codigo_raw, especFonteRecurso = self._split_codigo_especificacao(
            FonteRecurso
        )
        fonteRecursoCodigo = "".join(filter(str.isdigit, fonteRecurso_codigo_raw))
        fonteRecurso = LoaModels.Fonte.objects.filter(
            loa__ano=data.year, codigo__iexact=fonteRecursoCodigo
        ).first()
        if not fonteRecurso:
            fonteRecurso = LoaModels.Fonte()
            fonteRecurso.loa_id = loa.id
            fonteRecurso.especificacao = especFonteRecurso
            fonteRecurso.codigo = fonteRecursoCodigo
            fonteRecurso.save()

        destinacaoRecurso_codigo_raw, especDestinacaoRecurso = (
            self._split_codigo_especificacao(DestinacaoRecurso)
        )
        destinacaoRecursoCodigo = "".join(
            filter(str.isdigit, destinacaoRecurso_codigo_raw)
        )
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

        md["scrap"]["values"] = {
            "Data": dataItem,
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

        empenho.nome = Fornecedor
        empenho.cpfcnpj = CpfCnpjCredor
        if len(CpfCnpjCredor) == 14:
            empenho.cpfcnpj = f"{CpfCnpjCredor[:3]}.***.***-{CpfCnpjCredor[12:]}"
            md["scrap"]["values"]["CpfCnpjCredor"] = empenho.cpfcnpj

        empenho.data = data
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
        return (empenho, created)

    def fetch_empenhos(self, endpoint, payload):
        response_text = None
        response = None
        pagina = payload.get("page", {}).get("number")
        periodo = f"{payload.get('dataInicio')} a {payload.get('dataFim')}"
        try:
            # headers locais mesclados com o User-Agent padrão do módulo,
            # que antes era sobrescrito (shadowing) e nunca chegava a ser enviado
            request_headers = {**DEFAULT_HEADERS, "Content-Type": "application/json"}
            response = requests.post(endpoint, json=payload, headers=request_headers)

            # Dispara uma exceção se o status code for um erro
            response.raise_for_status()
            response_text = response.text

        except requests.exceptions.HTTPError as errh:
            print(
                f"[scrap_centi] ERRO HTTP ao buscar página {pagina} ({periodo}): {errh}"
            )
            self.logger.error(
                f"Erro HTTP ao buscar empenhos página={pagina} periodo={periodo}: "
                f"{errh} | resposta={response.text if response is not None else ''}"
            )
        except requests.exceptions.RequestException as err:
            print(
                f"[scrap_centi] ERRO de conexão ao buscar página {pagina} "
                f"({periodo}): {err}"
            )
            self.logger.error(
                f"Erro de conexão ao buscar empenhos página={pagina} "
                f"periodo={periodo}: {err}"
            )
        except Exception as err:
            print(f"[scrap_centi] ERRO inesperado ao buscar página {pagina}: {err}")
            self.logger.error(
                f"Erro inesperado ao buscar empenhos página={pagina} "
                f"periodo={periodo}: {err}",
                exc_info=True,
            )

        if not response_text:
            return []

        try:
            dados = json.loads(response_text)
        except json.JSONDecodeError:
            try:
                texto_limpo = sanitize_json_content(response_text)
                dados = json.loads(texto_limpo)
                print(
                    f"[scrap_centi] JSON da página {pagina} precisou de correção "
                    f"automática."
                )
            except json.JSONDecodeError as e2:
                print(
                    f"[scrap_centi] ERRO: falha ao corrigir JSON da página "
                    f"{pagina}: {e2}"
                )
                self.logger.error(
                    f"Falha ao corrigir JSON de empenhos página={pagina} "
                    f"periodo={periodo}: {e2}"
                )
                dados = []

        return dados
