import pytest

from cmj.search.fts import build_fts_queries, extract_terms
from cmj.search.models import Embedding

pytestmark = pytest.mark.django_db


def test_extract_terms_remove_pontuacao_duplicatas_e_letras_soltas():
    assert extract_terms('Asfalto, "pátios"; de a asfalto (Pátios)') == [
        ["Asfalto"],
        ["pátios"],
        ["de"],
    ]


def test_extract_terms_gera_variantes_de_numero_de_lei():
    assert extract_terms("4353") == [["4353", "4.353"]]
    assert extract_terms("4.353") == [["4.353", "4353"]]
    assert extract_terms("1234567") == [["1234567", "1.234.567"]]
    assert extract_terms("0123") == [["0123"]]
    assert extract_terms("12/2020") == [["12/2020"]]


def test_extract_terms_limita_quantidade():
    assert len(extract_terms(" ".join(f"termo{i}" for i in range(50)))) == 12


def test_build_fts_queries():
    assert build_fts_queries("") == (None, None)
    assert build_fts_queries("...") == (None, None)

    query_and, query_or = build_fts_queries("asfalto")
    assert query_and is not None and query_or is None

    query_and, query_or = build_fts_queries("asfalto pátios")
    assert query_and is not None and query_or is not None


@pytest.fixture
def embeddings(db):
    def make(chunk):
        emb = Embedding.objects.create(chunk=chunk)
        emb.update_search_vector()
        return emb

    return {
        "ambos": make("Fica autorizada a pavimentação e o asfalto de pátios."),
        "um": make("O asfalto será pago pela prefeitura."),
        "nenhum": make("Dispõe sobre licença maternidade."),
        "lei": make("Altera a Lei nº 4.353 de 2020."),
    }


@pytest.mark.django_db
def test_fts_ids_and_vem_antes_do_or(embeddings):
    ids = Embedding._fts_ids("asfalto pavimentação", 10)

    assert ids == [embeddings["ambos"].id, embeddings["um"].id]


@pytest.mark.django_db
def test_fts_ids_respeita_limite_e_nao_repete(embeddings):
    ids = Embedding._fts_ids("asfalto pavimentação", 1)

    assert ids == [embeddings["ambos"].id]
    assert len(set(Embedding._fts_ids("asfalto pavimentação", 10))) == 2


@pytest.mark.django_db
def test_fts_ids_encontra_numero_com_ou_sem_ponto(embeddings):
    assert Embedding._fts_ids("4353", 10) == [embeddings["lei"].id]
    assert Embedding._fts_ids("4.353", 10) == [embeddings["lei"].id]


@pytest.mark.django_db
def test_fts_ids_consulta_vazia_ou_so_stopwords(embeddings):
    assert Embedding._fts_ids("", 10) == []
    assert Embedding._fts_ids("de", 10) == []
