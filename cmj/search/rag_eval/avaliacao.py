"""
Métricas de avaliação da recuperação do chat RAG, no nível de artigo.

Cada chunk recuperado é mapeado ao artigo mais externo que o contém
(`ArtigoKey`); a lista de artigos distintos, na ordem de relevância, é
comparada com os artigos esperados de cada pergunta.
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

PERGUNTAS_PADRAO = Path(__file__).with_name("perguntas_referencia.json")
KS = (1, 3, 5, 10, 20)


@dataclass(frozen=True)
class ArtigoKey:
    ta_id: int
    artigo: str
    ordem: int


def normalizar_artigo(rotulo):
    return re.sub(r"\s+", " ", rotulo or "").strip().rstrip(".")


def carregar_perguntas(caminho=PERGUNTAS_PADRAO):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)["perguntas"]


def casa(esperado, chave):
    """O artigo recuperado é o esperado? `ordem` é opcional (desambigua rótulos repetidos)."""
    if chave is None or chave.ta_id != esperado["ta_id"]:
        return False
    if normalizar_artigo(chave.artigo) != normalizar_artigo(esperado["artigo"]):
        return False
    return esperado.get("ordem") in (None, chave.ordem)


def artigos_distintos(chaves):
    """Remove repetições mantendo a primeira posição; ignora chunks sem artigo (None)."""
    vistos = set()
    resultado = []
    for chave in chaves:
        if chave is None or chave in vistos:
            continue
        vistos.add(chave)
        resultado.append(chave)
    return resultado


def melhor_posicao(artigos, esperados):
    """Posição (base 1) do primeiro artigo esperado na lista, ou None."""
    for posicao, chave in enumerate(artigos, start=1):
        if any(casa(e, chave) for e in esperados):
            return posicao
    return None


def agregar(resultados):
    """
    `resultados`: dicts com `categoria`, `posicao` (int|None), `artigos` e `chunks`.
    Retorna métricas gerais e por categoria.
    """

    def resumo(itens):
        n = len(itens)
        if not n:
            return {}
        posicoes = [i["posicao"] for i in itens]
        return {
            "n": n,
            **{
                f"hit@{k}": sum(1 for p in posicoes if p is not None and p <= k) / n
                for k in KS
            },
            "mrr": sum(1 / p for p in posicoes if p) / n,
            "nao_encontradas": sum(1 for p in posicoes if p is None),
            "artigos_medio": sum(i["artigos"] for i in itens) / n,
            "chunks_medio": sum(i["chunks"] for i in itens) / n,
        }

    por_categoria = defaultdict(list)
    for r in resultados:
        por_categoria[r["categoria"]].append(r)
    return {
        "geral": resumo(resultados),
        "categorias": {c: resumo(itens) for c, itens in sorted(por_categoria.items())},
    }
