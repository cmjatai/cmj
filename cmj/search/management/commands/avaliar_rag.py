import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cmj.search.fts import RANKER_PADRAO, RANKERS
from cmj.search.models import Embedding
from cmj.search.rag_eval.avaliacao import (
    KS,
    PERGUNTAS_PADRAO,
    ArtigoKey,
    agregar,
    artigos_distintos,
    carregar_perguntas,
    melhor_posicao,
)
from sapl.compilacao.models import Dispositivo, TextoArticulado


class Command(BaseCommand):
    help = (
        "Avalia a recuperação do chat RAG (recall@k e MRR por artigo) com o conjunto "
        "de perguntas de referência, comparando estratégias de chunking."
    )

    def add_arguments(self, parser):
        parser.add_argument("--perguntas", default=str(PERGUNTAS_PADRAO))
        parser.add_argument(
            "--estrategias",
            nargs="+",
            choices=["v1", "v2"],
            default=["v1", "v2"],
            help="Estratégias a comparar (padrão: v1 v2).",
        )
        parser.add_argument(
            "--modo",
            choices=["textual", "hibrido"],
            default="textual",
            help="textual: só Full-Text Search (não usa a API). "
            "hibrido: busca semântica + textual, como no chat (chama a API do "
            "Gemini para embutir cada pergunta e exige vetores nos chunks).",
        )
        parser.add_argument("--top-k", type=int, default=60)
        parser.add_argument(
            "--rankers",
            nargs="+",
            choices=sorted(RANKERS),
            default=[RANKER_PADRAO],
            help="Funções de ranking do Full-Text Search a comparar (ver cmj/search/fts.py).",
        )
        parser.add_argument(
            "--v2-max-tokens",
            type=int,
            default=None,
            help="Orçamento de tokens por chunk na simulação da v2 (padrão: o do módulo).",
        )
        parser.add_argument(
            "--v2-sem-ementa",
            action="store_true",
            help="Simula a v2 sem a ementa da norma no cabeçalho dos chunks.",
        )
        parser.add_argument("--categoria", default=None)
        parser.add_argument(
            "--simular-v2",
            action="store_true",
            help="Gera os chunks v2 de todos os T.A. publicados dentro de uma "
            "transação que é DESFEITA ao final: avalia a v2 sem gravar nada. "
            "Só no modo textual (os chunks simulados não têm vetores).",
        )
        parser.add_argument(
            "--detalhe",
            action="store_true",
            help="Mostra a posição do artigo esperado em cada pergunta.",
        )
        parser.add_argument("--json-saida", default=None)

    def handle(self, *args, **options):
        if options["simular_v2"] and options["modo"] != "textual":
            raise CommandError("--simular-v2 só é possível no modo textual.")

        perguntas = carregar_perguntas(options["perguntas"])
        if options["categoria"]:
            perguntas = [p for p in perguntas if p["categoria"] == options["categoria"]]
        if not perguntas:
            raise CommandError("Nenhuma pergunta selecionada.")

        embeddings = {}
        if options["modo"] == "hibrido":
            from cmj.utils.genia import IAGenaiBase

            ia = IAGenaiBase()
            for p in perguntas:
                embeddings[p["id"]] = ia.get_query_embedding(p["pergunta"])

        variantes = [
            (estrategia, ranker)
            for estrategia in options["estrategias"]
            for ranker in options["rankers"]
        ]
        rotulos = [
            f"{e}/{r}" if len(options["rankers"]) > 1 else e for e, r in variantes
        ]

        with transaction.atomic():
            if options["simular_v2"]:
                opcoes = {"incluir_ementa": not options["v2_sem_ementa"]}
                if options["v2_max_tokens"]:
                    opcoes["max_tokens"] = options["v2_max_tokens"]
                self.simular_v2(opcoes)

            resultados = {
                rotulo: self.avaliar(
                    perguntas, estrategia, embeddings, options["top_k"], ranker
                )
                for rotulo, (estrategia, ranker) in zip(rotulos, variantes)
            }
            # nada é gravado na avaliação; na simulação, desfaz os chunks v2
            transaction.set_rollback(True)

        metricas = {e: agregar(r) for e, r in resultados.items()}
        self.imprimir(metricas, rotulos, len(perguntas), options)
        if options["detalhe"]:
            self.imprimir_detalhe(perguntas, resultados, rotulos)
        if options["json_saida"]:
            with open(options["json_saida"], "w", encoding="utf-8") as f:
                json.dump(
                    {"metricas": metricas, "resultados": resultados},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

    def simular_v2(self, opcoes):
        tas = TextoArticulado.objects.filter(editing_locked=True).order_by("pk")
        total = tas.count()
        self.stdout.write(
            f"Simulando chunks v2 de {total} T.A. {opcoes} (será desfeito)..."
        )
        for i, ta in enumerate(tas.iterator(chunk_size=200), start=1):
            if ta.is_revogado():
                continue
            ta.generate_chunks_v2(**opcoes)
            if i % 1000 == 0:
                self.stdout.write(f"  {i}/{total}")

    def cadeias(self, dispositivo_ids):
        """pk -> (pai_id, tipo, rotulo, ordem, ta_id) dos dispositivos e seus ancestrais."""
        dados = {}
        pendentes = set(dispositivo_ids)
        while pendentes:
            linhas = Dispositivo.objects.filter(pk__in=pendentes).values_list(
                "pk",
                "dispositivo_pai_id",
                "tipo_dispositivo__nome",
                "rotulo",
                "ordem",
                "ta_id",
            )
            novos = set()
            for pk, pai, tipo, rotulo, ordem, ta_id in linhas:
                dados[pk] = (pai, tipo, rotulo, ordem, ta_id)
                if pai and pai not in dados:
                    novos.add(pai)
            pendentes = novos - set(dados)
        return dados

    @staticmethod
    def artigo_externo(pk, dados):
        externo = None
        atual = pk
        while atual:
            pai, tipo, rotulo, ordem, ta_id = dados[atual]
            if tipo == "Artigo":
                externo = ArtigoKey(ta_id, rotulo, ordem)
            atual = pai
        return externo

    def avaliar(self, perguntas, estrategia, embeddings, top_k, ranker=None):
        resultados = []
        for p in perguntas:
            ids = Embedding.search_ids(
                p["pergunta"], embeddings.get(p["id"]), top_k, estrategia, ranker
            )
            mapa = Embedding.objects.in_bulk(ids)
            ordenados = [mapa[i] for i in ids if i in mapa]
            dados = self.cadeias({e.object_id for e in ordenados if e.object_id})
            chaves = [
                (
                    self.artigo_externo(e.object_id, dados)
                    if e.object_id in dados
                    else None
                )
                for e in ordenados
            ]
            artigos = artigos_distintos(chaves)
            resultados.append(
                {
                    "id": p["id"],
                    "categoria": p["categoria"],
                    "posicao": melhor_posicao(artigos, p["esperado"]),
                    "artigos": len(artigos),
                    "chunks": len(ordenados),
                }
            )
        return resultados

    def imprimir(self, metricas, estrategias, n, options):
        self.stdout.write(
            f"\nModo: {options['modo']} | top_k={options['top_k']} | perguntas: {n}"
            + (" | v2 SIMULADA (desfeita)" if options["simular_v2"] else "")
        )
        colunas = ["hit@%d" % k for k in KS] + ["mrr", "nao_encontradas"]
        cab = f"{'':<24}" + "".join(f"{e:>10}" for e in estrategias)

        def linha(rotulo, chave, grupo):
            valores = []
            for e in estrategias:
                v = grupo(metricas[e]).get(chave)
                if v is None:
                    valores.append(f"{'-':>10}")
                elif chave == "nao_encontradas":
                    valores.append(f"{v:>10d}")
                else:
                    valores.append(f"{v:>10.3f}")
            self.stdout.write(f"{rotulo:<24}" + "".join(valores))

        self.stdout.write("\n== GERAL ==\n" + cab)
        for chave in colunas:
            linha(chave, chave, lambda m: m["geral"])
        for extra in ("artigos_medio", "chunks_medio"):
            linha(extra, extra, lambda m: m["geral"])

        categorias = sorted({c for m in metricas.values() for c in m["categorias"]})
        self.stdout.write("\n== POR CATEGORIA (hit@5 / hit@20 / mrr) ==")
        for categoria in categorias:
            self.stdout.write(f"[{categoria}]")
            for chave in ("hit@5", "hit@20", "mrr"):
                linha(
                    f"  {chave}",
                    chave,
                    lambda m, c=categoria: m["categorias"].get(c, {}),
                )

    def imprimir_detalhe(self, perguntas, resultados, estrategias):
        self.stdout.write("\n== POSIÇÃO DO ARTIGO ESPERADO (· = não encontrado) ==")
        for i, p in enumerate(perguntas):
            posicoes = [
                str(resultados[e][i]["posicao"] or "·").rjust(4) for e in estrategias
            ]
            self.stdout.write(
                f"{p['id']} [{p['categoria']:<19}] "
                + " ".join(f"{e}:{x}" for e, x in zip(estrategias, posicoes))
                + f"  {p['pergunta'][:70]}"
            )
