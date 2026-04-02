import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO

from bs4 import BeautifulSoup as bs
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import CASCADE
from django.db.models.fields.json import JSONField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cmj.loa.models.financeiro_execucao import DespesaPaga, Empenho, ReceitaArrecadada
from cmj.loa.models.financeiro_orcamento import (
    Acao,
    Fonte,
    Funcao,
    Natureza,
    Orgao,
    Programa,
    ReceitaOrcamentaria,
    SubFuncao,
    UnidadeOrcamentaria,
)
from cmj.loa.models.loa import Loa
from cmj.utils import quantize


class ScrapRecord(models.Model):

    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=None,
        encoder=DjangoJSONEncoder,
    )

    mes = models.PositiveSmallIntegerField(verbose_name=_("Mes"))
    ano = models.PositiveSmallIntegerField(verbose_name=_("Ano"))
    orgao = models.TextField(verbose_name=_("Órgão"))

    codigo = models.TextField(verbose_name=_("Código"), default="")

    url = models.TextField(verbose_name=_("Órgão"), unique=True)

    content = models.BinaryField(editable=True, default=b"")

    modified = models.DateTimeField(
        verbose_name=_("modified"), editable=False, auto_now=True
    )

    erro = models.BooleanField(default=False)

    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        default=None,
        related_name="scrap_set",
        on_delete=CASCADE,
    )

    class Meta:
        verbose_name = "ScrapRecord"
        verbose_name_plural = "ScrapRecord"
        ordering = ["id"]

    def clean_text(self, text):
        while "  " in text:
            text = text.replace("  ", " ")
        while " \n" in text:
            text = text.replace(" \n", "\n")
        while "\n " in text:
            text = text.replace("\n ", "\n")
        while "\r\n" in text:
            text = text.replace("\r\n", "\n")
        while "\n\n" in text:
            text = text.replace("\n\n", "\n")
        while "<td> " in text:
            text = text.replace("<td> ", "<td>")
        while " :</td>" in text:
            text = text.replace(" :</td>", ":</td>")
        while "\n</td>" in text:
            text = text.replace("\n</td>", "</td>")
        while " </td>" in text:
            text = text.replace(" </td>", "</td>")
        while "<td>R$ " in text:
            text = text.replace("<td>R$ ", "<td>")
        return text

    def update_data_models(self):

        try:
            # with transaction.atomic():
            if "empenhada" in self.metadata["url_dict"]["name"]:
                if not self.codigo:
                    return None
                self._update_empenho()
                return
            if "despesa" in self.metadata["url_dict"]["name"]:
                if not self.codigo or self.codigo == "TOTAL:":
                    return None
                self._update_despesa_paga()
            elif "receita" in self.metadata["url_dict"]["name"]:
                if not self.codigo or self.codigo == "TOTAL:":
                    return None
                self._update_receita_arrecadada()
            elif "transferencia" in self.metadata["url_dict"]["name"]:
                self._update_transferencia_recursos()
            if self.erro:
                self.erro = False
                self.save(update_fields=("erro",))
        except Exception as e:
            self.erro = True
            self.save(update_fields=("erro",))

    def _update_empenho(self):
        org = Orgao.objects.get(codigo=self.orgao, loa__ano=self.ano)
        empenho = Empenho.objects.filter(codigo=self.codigo, orgao=org).first()

        if not empenho:
            empenho = Empenho()

        item_list = self.metadata["item_list"]
        dt = datetime.strptime(item_list[1], "%d/%m/%Y").date()

        (
            codigo,
            data,
            fornecedor,
            cpfcnpj,
            processo,
            modalidade,
            valor_empenhado,
            valor_anulado,
            valor_liquidado,
            valor_pago_bruto,
        ) = item_list

        valor_empenhado = Decimal(valor_empenhado.replace(".", "").replace(",", "."))
        valor_anulado = Decimal(valor_anulado.replace(".", "").replace(",", "."))
        valor_liquidado = Decimal(valor_liquidado.replace(".", "").replace(",", "."))
        valor_pago_bruto = Decimal(valor_pago_bruto.replace(".", "").replace(",", "."))

        empenho.codigo = codigo
        empenho.orgao = org

        empenho.data = dt
        empenho.nome = fornecedor
        empenho.cpfcnpj = cpfcnpj
        empenho.processo = processo
        empenho.modalidade = modalidade
        empenho.valor_empenhado = valor_empenhado
        empenho.valor_anulado = valor_anulado
        empenho.valor_liquidado = valor_liquidado
        empenho.valor_pago_bruto = valor_pago_bruto

        values = {}
        if self.metadata["url_dict"]["format"] != "html":
            if settings.DEBUG:
                print(
                    "             ",
                    timezone.localtime(),
                    "Empenho Create:",
                    empenho.codigo,
                    empenho.data,
                    empenho.valor_empenhado,
                    empenho.nome,
                )
        else:
            if settings.DEBUG:
                print(
                    "             ",
                    timezone.localtime(),
                    "Empenho Update:",
                    empenho.codigo,
                    empenho.data,
                    empenho.valor_empenhado,
                    empenho.nome,
                )
            content = self.content
            if not isinstance(content, bytes):
                content = content.tobytes()
            content = content.decode("utf-8-sig")
            content = self.clean_text(self.clean_text(self.clean_text(content)))
            tables = bs(content, "html.parser").findAll("table")
            if tables:
                for row in tables[0].findAll("tr"):
                    cols = row.findAll("td")
                    values[cols[0].text] = cols[1].text.strip()

                empenho.metadata = empenho.metadata or {}
                empenho.metadata["scrap"] = {"values": values}

                # exemplo do conteúdo de values
                # values = {'Código:': '401179', 'Data:': '30/03/2026', 'Fornecedor:': 'TOTAL SEGURANÇA EQUIPAMENTOS DE PROTEÇÃO E SERVIÇOS ESPECIALIZADOS LTDA - ME', 'Órgão:': '03 - PREFEITURA MUNICIPAL DE JATAI', 'Programa:': '1539 - AVANÇO NAS MELHORIAS DOS SERVIÇOS DE DESENVOLVIMENTO URBANO', 'Unidade:': '11 - SECRETARIA DE OBRAS E PLANEJAMENTO URBANO', 'Função:': '15 - URBANISMO', 'Dotação:': '1539.11.2039.15.451.339030', 'Sub-Função:': '451 - INFRA-ESTRUTURA URBANA', 'Projeto / Atividade:': '2039 - MANUTENÇÃO SECRETARIA DE OBRAS E PLANEJAMENTO URBANO', 'Elemento:': '339030 - MATERIAL DE CONSUMO', 'Sub-Elemento:': '28 - MATERIAL DE PROTECAO E SEGURANCA', 'Modalidade:': 'PREGÃO', 'Número da Licitação:': '76', 'Fonte de Recursos:': '100 - RECURSOS NÃO VINCULADOS DE IMPOSTOS', 'Histórico:': 'CONTRATAÇÃO DE EMPRESA VISANDO A AQUISIÇÃO DE TRAJES RETARDANTES COM FAIXA REFLEXIVA PARA ATENDIMENTO À DEMANDA DA SECRETARIA MUNICIPAL DE OBRAS E PLANEJAMENTO URBANO (ARP Nº 18/2025 - PREGÃO ELETRÔNICO Nº 76/2025 - PROC. ADM. Nº 32845/2025).'}
                empenho.nome = values.get("Fornecedor:", "") or values.get(
                    "Fornecedor", ""
                )
                empenho.dotacao = values.get("Dotação:", "") or values.get(
                    "Dotação", ""
                )
                empenho.historico = values.get("Histórico:", "") or values.get(
                    "Histórico", ""
                )
                empenho.numero_licitacao = values.get(
                    "Número da Licitação:", ""
                ) or values.get("Número da Licitação", "")
                empenho.modalidade = values.get("Modalidade:", "") or values.get(
                    "Modalidade", ""
                )

                fks = {
                    "Programa:": Programa,
                    "Unidade:": UnidadeOrcamentaria,
                    "Função:": Funcao,
                    "Sub-Função:": SubFuncao,
                    "Projeto / Atividade:": Acao,
                    "Fonte de Recursos:": Fonte,
                }
                for key, model in fks.items():
                    try:
                        if key in values:
                            codigo, especificacao = values[key].split(" - ", 1)
                            params = {
                                "loa": Loa.objects.get(ano=self.ano),
                                "codigo": codigo,
                            }
                            if key == "Unidade:":
                                params["orgao"] = Orgao.objects.get(
                                    codigo=self.orgao, loa__ano=self.ano
                                )
                            if key == "Sub-Função:":
                                params["funcao"] = Funcao.objects.get(
                                    loa__ano=self.ano,
                                    codigo=values.get("Função:", "").split(" - ")[0],
                                )
                            fk_instance = model.objects.get_or_create(
                                **params,
                                defaults={"especificacao": especificacao},
                            )
                            setattr(empenho, empenho.mapeamento[key], fk_instance[0])
                    except Exception as e:
                        print(f"Erro ao processar {key}: {e}")
                        print(f"Valor problemático: {values.get(key, '')}")

                try:
                    elemento = values.get("Elemento:", "") or values.get("Elemento", "")
                    subelemento = values.get("Sub-Elemento:", "") or values.get(
                        "Sub-Elemento", ""
                    )
                    codigo_elemento, espec_elemento = (
                        elemento.split(" - ")[0] if " - " in elemento else elemento,
                        elemento.split(" - ")[1] if " - " in elemento else elemento,
                    )
                    codigo_subelemento, espec_subelemento = (
                        (
                            subelemento.split(" - ", 1)[0]
                            if " - " in subelemento
                            else subelemento
                        ),
                        (
                            subelemento.split(" - ", 1)[1]
                            if " - " in subelemento
                            else subelemento
                        ),
                    )
                    codigo_natureza = f"{codigo_elemento}{codigo_subelemento}"
                    # formatar codigo_natureza para a mascara: 9.9.99.99.99
                    codigo_natureza_formatado = f"{codigo_natureza[0]}.{codigo_natureza[1]}.{codigo_natureza[2:4]}.{codigo_natureza[4:6]}.{codigo_natureza[6:]}"

                    if codigo_elemento and codigo_subelemento:
                        natureza_instance = Natureza.objects.get_or_create(
                            loa=Loa.objects.get(ano=self.ano),
                            codigo=codigo_natureza_formatado,
                            defaults={
                                "especificacao": (
                                    espec_subelemento
                                    if espec_subelemento
                                    else (espec_elemento or elemento)
                                )
                            },
                        )
                        empenho.natureza = natureza_instance[0]
                except Exception as e:
                    print(f"Erro ao processar Elemento/Sub-Elemento: {e}")
                    print(
                        f"Valor problemático: {values.get('Elemento:', '')} / {values.get('Sub-Elemento:', '')}"
                    )
        empenho.save()

        return

        if self.metadata["url_dict"]["format"] == "csv":
            print("csv")

            content = self.content
            if not isinstance(content, bytes):
                content = content.tobytes()

            content = content.decode("utf-8-sig")
            file = StringIO(content)
            csv_data = csv.reader(file, delimiter=";")

            lista = list(csv_data)
            print(lista)

    def _update_transferencia_recursos(self):

        if self.metadata["url_dict"]["format"] != "csv":
            return None
        org = Orgao.objects.get(codigo=self.orgao, loa__ano=self.ano)

        content = self.content
        if isinstance(content, memoryview):
            content = content.tobytes()
        content = content.decode("utf-8-sig")
        file = StringIO(content)
        csv_data = csv.reader(file, delimiter=";")

        lista = list(csv_data)[1:]

        for row in lista:

            dt = datetime.strptime(row[0], "%d/%m/%Y").date()

            valor = Decimal(row[4].replace(".", "").replace(",", "."))

            ro, created = ReceitaOrcamentaria.objects.get_or_create(
                codigo=row[1], orgao=org
            )

            if row[2] == "Despesa":
                valor = quantize(valor * Decimal(-1))

            ra = ReceitaArrecadada.objects.get_or_create(
                receita=ro, data=dt, historico=row[1], tipo=row[2], valor=valor
            )

    def _update_receita_arrecadada(self):
        if self.metadata["url_dict"]["format"] != "csv":
            return None
        org = Orgao.objects.get(codigo=self.orgao, loa__ano=self.ano)

        ro, created = ReceitaOrcamentaria.objects.get_or_create(
            codigo=self.codigo, orgao=org
        )

        # if self.codigo != '11130311' or org.codigo != '03':
        #    return

        item_list = self.metadata["item_list"]
        ro.historico = item_list[1]
        ro.valor = Decimal(item_list[2].replace(".", "").replace(",", "."))
        ro.save()

        content = self.content
        if isinstance(content, memoryview):
            content = content.tobytes()
        content = content.decode("utf-8-sig")
        file = StringIO(content)
        csv_data = csv.reader(file, delimiter=";")

        lista = list(csv_data)
        idx_init = 0
        for idx_init, row in enumerate(lista):
            if not row[0]:
                break

        idx_init += 2
        rows = lista[idx_init:]

        rows = sorted(
            rows, key=lambda x: [tuple(map(int, x[0].split("/")[::-1])), x[1], x[3]]
        )

        rows_filtered = []
        rows = list(enumerate(rows))
        for idx, row in rows:
            # rows_filtered.append(row)
            # continue

            if not idx or "RETENÇÃO" not in row[2]:
                rows_filtered.append(row)
                continue

            if rows[idx][1] == rows[idx - 1][1]:
                continue

            rows_filtered.append(row)

        rows = rows_filtered

        if ro.receitaarrecadada_set.count() >= len(rows):
            return
        ro.receitaarrecadada_set.filter().delete()

        for row in rows:
            dt = datetime.strptime(row[0], "%d/%m/%Y").date()
            # print(self.codigo, row)

            valor = Decimal(row[3].replace(".", "").replace(",", "."))

            # if row[2] == 'RETENÇÃO DE EMPENHO':
            #    ra = ReceitaArrecadada.objects.filter(
            #        receita=ro,
            #        historico=row[1],
            #        data=dt,
            #        valor=valor
            #    ).first()
            #    if ra:
            #        continue

            ra = ReceitaArrecadada()
            ra.receita = ro
            ra.data = dt
            ra.historico = row[1]
            ra.tipo = row[2]
            ra.valor = valor
            ra.save()

    def _update_despesa_paga(self):

        org = Orgao.objects.get(codigo=self.orgao, loa__ano=self.ano)
        dp = DespesaPaga.objects.filter(codigo=self.codigo, orgao=org).first()

        item_list = self.metadata["item_list"]
        dt = datetime.strptime(item_list[1], "%d/%m/%Y").date()
        valor = Decimal(item_list[-1].replace(".", "").replace(",", "."))

        if dp and dp.valor == valor and dp.data == dt and dp.natureza:
            return dp

        if dp and self.metadata["url_dict"]["format"] == "csv":
            return dp

        values = {}
        unidade = None
        natureza = None
        fonte = None

        if self.metadata["url_dict"]["format"] == "html":
            content = self.content
            if not isinstance(content, bytes):
                content = content.tobytes()
            content = content.decode("utf-8-sig")
            content = self.clean_text(self.clean_text(self.clean_text(content)))
            tables = bs(content, "html.parser").findAll("table")
            if not tables:
                return None
            for row in tables[0].findAll("tr"):
                cols = row.findAll("td")
                values[cols[0].text] = cols[1].text

            unidade = UnidadeOrcamentaria.objects.filter(
                orgao=org, loa__ano=self.ano, codigo=values["Unidade Financeira:"][:2]
            ).first()

            try:
                nat = values["Elemento:"]
                natureza = Natureza.objects.filter(
                    loa__ano=self.ano,
                    codigo=f"{nat[0]}.{nat[1]}.{nat[2:4]}.{nat[4:6]}.00",
                ).first()
            except:
                natureza = None

            try:
                fontestr = values["Fonte de Recursos:"]
                fonte, created = Fonte.objects.get_or_create(
                    loa_id=self.ano, codigo=fontestr[0:3]
                )
                if fonte.especificacao != fontestr[6:]:
                    fonte.especificacao = fontestr[6:]
                    fonte.save()
            except:
                fonte = None

        dp, created = DespesaPaga.objects.get_or_create(
            codigo=self.codigo,
            orgao=org,
        )

        dp.metadata = dp.metadata or {}
        dp.metadata["scrap"] = {"values": values}

        dp.cpfcnpj = item_list[3]
        dp.nome = item_list[2]
        dp.tipo = item_list[4]
        dp.historico = values.get("Historico:", None)

        dp.unidade = unidade
        dp.natureza = natureza
        dp.fonte = fonte

        dp.valor = valor
        dp.data = dt
        dp.save()

        return dp
