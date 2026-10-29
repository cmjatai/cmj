from types import SimpleNamespace
from unittest import mock

import pytest

from cmj.search.models import Embedding
from cmj.utils.genia import IAGenaiBase

VECTOR = [0.1] * 1536

pytestmark = pytest.mark.django_db


@pytest.fixture
def ia():
    with mock.patch("cmj.utils.genia.genai.Client") as client_cls, mock.patch(
        "cmj.utils.genia.time.sleep"
    ):
        instance = IAGenaiBase()
        instance.client = client_cls.return_value
        yield instance


def _response(n):
    return SimpleNamespace(embeddings=[SimpleNamespace(values=VECTOR)] * n)


def _docs(n):
    return [{"text": f"texto {i}", "title": None} for i in range(n)]


def test_embed_documents_repete_em_falha_transitoria(ia):
    ia.client.models.embed_content.side_effect = [RuntimeError("429"), _response(2)]

    assert ia.embed_documents(_docs(2)) == [VECTOR, VECTOR]
    assert ia.client.models.embed_content.call_count == 2


def test_embed_documents_isola_documento_problematico(ia):
    def embed_content(model, contents, config):
        if len(contents) > 1 or "texto 1" in contents[0]:
            raise RuntimeError("limite de tokens")
        return _response(1)

    ia.client.models.embed_content.side_effect = embed_content

    assert ia.embed_documents(_docs(3)) == [VECTOR, None, VECTOR]


def test_embed_documents_interrompe_quando_api_fora_do_ar(ia):
    ia.client.models.embed_content.side_effect = RuntimeError("fora do ar")

    result = ia.embed_documents(_docs(10), batch_size=2)

    # 2 lotes seguidos totalmente falhos interrompem; os 6 restantes nem são tentados
    assert result == [None, None, None, None]


@pytest.mark.django_db
def test_generate_embeddings_for_queryset_grava_progresso_e_deixa_pendentes(db):
    ok = Embedding.objects.create(chunk="a")
    falho = Embedding.objects.create(chunk="b")

    with mock.patch("cmj.search.models.IAGenaiBase") as ia_cls:
        ia_cls.return_value.embed_documents.return_value = [VECTOR, None]
        done = Embedding.generate_embeddings_for_queryset(
            Embedding.objects.filter(id__in=[ok.id, falho.id])
        )

    assert done == 1
    assert list(Embedding.objects.filter(vetor1536__isnull=True)) == [falho]


@pytest.mark.django_db
def test_generate_embeddings_for_queryset_vazio(db):
    assert Embedding.generate_embeddings_for_queryset(Embedding.objects.none()) == 0
