import pytest

from cmj.search.rag_eval.avaliacao import (
    ArtigoKey,
    agregar,
    artigos_distintos,
    carregar_perguntas,
    casa,
    melhor_posicao,
    normalizar_artigo,
    porte_da_norma,
)

pytestmark = pytest.mark.django_db


def test_normalizar_artigo():
    assert normalizar_artigo("  Art.  5º. ") == "Art. 5º"
    assert normalizar_artigo(None) == ""


def test_casa_com_e_sem_ordem():
    chave = ArtigoKey(7, "Art. 153.", 3145000)

    assert casa({"ta_id": 7, "artigo": "Art. 153"}, chave)
    assert casa({"ta_id": 7, "artigo": "Art. 153", "ordem": 3145000}, chave)
    assert not casa({"ta_id": 7, "artigo": "Art. 153", "ordem": 1}, chave)
    assert not casa({"ta_id": 8, "artigo": "Art. 153"}, chave)
    assert not casa({"ta_id": 7, "artigo": "Art. 154"}, chave)
    assert not casa({"ta_id": 7, "artigo": "Art. 153"}, None)


def test_artigos_distintos_mantem_primeira_posicao_e_ignora_none():
    a, b = ArtigoKey(1, "Art. 1º", 10), ArtigoKey(1, "Art. 2º", 20)

    assert artigos_distintos([a, None, b, a, b]) == [a, b]


def test_melhor_posicao():
    a, b, c = (ArtigoKey(1, f"Art. {i}º", i) for i in (1, 2, 3))
    esperados = [{"ta_id": 1, "artigo": "Art. 3º"}, {"ta_id": 1, "artigo": "Art. 2º"}]

    assert melhor_posicao([a, b, c], esperados) == 2
    assert melhor_posicao([a], esperados) is None


def test_agregar_metricas_gerais_e_por_categoria():
    resultados = [
        {"categoria": "x", "posicao": 1, "artigos": 10, "chunks": 20},
        {"categoria": "x", "posicao": 4, "artigos": 20, "chunks": 40},
        {"categoria": "y", "posicao": None, "artigos": 30, "chunks": 60},
        {"categoria": "y", "posicao": 25, "artigos": 30, "chunks": 60},
    ]

    metricas = agregar(resultados)
    geral = metricas["geral"]

    assert geral["n"] == 4
    assert geral["hit@1"] == 0.25 and geral["hit@5"] == 0.5 and geral["hit@20"] == 0.5
    assert geral["mrr"] == pytest.approx((1 + 0.25 + 0 + 0.04) / 4)
    assert geral["nao_encontradas"] == 1
    assert geral["artigos_medio"] == 22.5
    assert metricas["categorias"]["x"]["hit@5"] == 1.0
    assert metricas["categorias"]["y"]["hit@20"] == 0.0


def test_porte_da_norma():
    assert [porte_da_norma(n) for n in (0, 9, 10, 49, 50, 199, 200, 458)] == [
        "pequena",
        "pequena",
        "média",
        "média",
        "grande",
        "grande",
        "muito grande",
        "muito grande",
    ]


def test_agregar_por_porte():
    resultados = [
        {"categoria": "x", "porte": "pequena", "posicao": 1, "artigos": 1, "chunks": 1},
        {
            "categoria": "x",
            "porte": "muito grande",
            "posicao": None,
            "artigos": 1,
            "chunks": 1,
        },
        {
            "categoria": "x",
            "porte": "muito grande",
            "posicao": 2,
            "artigos": 1,
            "chunks": 1,
        },
    ]

    portes = agregar(resultados)["portes"]

    assert list(portes) == ["pequena", "muito grande"]  # ordem de PORTES
    assert portes["pequena"]["hit@1"] == 1.0
    assert portes["muito grande"]["n"] == 2
    assert (
        portes["muito grande"]["hit@1"] == 0.0
        and portes["muito grande"]["hit@5"] == 0.5
    )


def test_conjunto_de_perguntas_de_referencia_e_consistente():
    perguntas = carregar_perguntas()

    assert len(perguntas) >= 90
    assert len({p["id"] for p in perguntas}) == len(perguntas)
    categorias = {p["categoria"] for p in perguntas}
    assert categorias >= {"parafrase", "contexto-da-norma", "dispositivo-interno"}
    for p in perguntas:
        assert p["pergunta"].strip().endswith("?")
        assert p["esperado"] and all(
            e["ta_id"] and e["artigo"].startswith("Art.") for e in p["esperado"]
        )
    # normas grandes (Código Tributário, Estatutos, Lei Orgânica) estão bem representadas
    grandes = {1117, 1, 1210, 281}
    assert sum(1 for p in perguntas if p["esperado"][0]["ta_id"] in grandes) >= 30
