import datetime

import pytest

from django.contrib.contenttypes.models import ContentType

from cmj.search.fts import RANKERS
from cmj.search.models import Embedding
from sapl.compilacao.models import Dispositivo, TextoArticulado, TipoDispositivo

pytestmark = pytest.mark.django_db


def _embedding(chunk, **metadata):
    emb = Embedding.objects.create(chunk=chunk, metadata=metadata)
    emb.update_search_vector()
    return emb


def test_strategy_filter_separa_v1_e_v2():
    v1 = _embedding("licença maternidade servidora")
    v2 = _embedding("licença maternidade servidora", chunk_strategy="v2")

    assert list(Embedding.objects.filter(Embedding.strategy_filter("v1"))) == [v1]
    assert list(Embedding.objects.filter(Embedding.strategy_filter("v2"))) == [v2]


def test_strategy_filter_padrao_vem_do_settings(settings):
    v1 = _embedding("a")
    v2 = _embedding("a", chunk_strategy="v2")

    settings.RAG_CHUNK_STRATEGY = "v2"
    assert list(Embedding.objects.filter(Embedding.strategy_filter())) == [v2]
    settings.RAG_CHUNK_STRATEGY = "v1"
    assert list(Embedding.objects.filter(Embedding.strategy_filter())) == [v1]


def test_fts_ids_respeita_a_estrategia():
    v1 = _embedding("asfalto de pátios")
    v2 = _embedding("asfalto de pátios", chunk_strategy="v2")

    assert Embedding._fts_ids("asfalto", 10, "v1") == [v1.id]
    assert Embedding._fts_ids("asfalto", 10, "v2") == [v2.id]


def test_search_ids_so_textual_quando_nao_ha_embedding_da_consulta():
    emb = _embedding("pavimentação de ruas")
    _embedding("outro assunto qualquer")

    assert Embedding.search_ids("pavimentação", None, 10, "v1") == [emb.id]


def test_desempate_do_ranking_e_deterministico_por_id():
    primeiro = _embedding("asfalto")
    segundo = _embedding("asfalto")

    assert Embedding._fts_ids("asfalto", 10, "v1") == [primeiro.id, segundo.id]


@pytest.mark.parametrize("ranker", sorted(RANKERS))
def test_todos_os_rankers_executam(ranker):
    emb = _embedding("pavimentação de ruas e avenidas")

    assert Embedding._fts_ids("pavimentação ruas", 10, "v1", ranker) == [emb.id]


def test_ranker_desconhecido_e_rejeitado():
    with pytest.raises(KeyError):
        Embedding._fts_ids("asfalto", 10, "v1", "inexistente")


def _norma_com_dois_artigos():
    """T.A. mínimo: Articulação > 2 x (Artigo > Caput), criado direto nos modelos."""
    ta = TextoArticulado.objects.create(
        ementa="", observacao="", numero=1, ano=2020, editing_locked=True
    )
    campos = dict(
        class_css="",
        rotulo_prefixo_html="",
        rotulo_prefixo_texto="",
        rotulo_ordinal=0,
        rotulo_sufixo_texto="",
        rotulo_sufixo_html="",
        texto_prefixo_html="",
        texto_sufixo_html="",
        nota_automatica_prefixo_html="",
        nota_automatica_sufixo_html="",
    )
    tipos = {
        nome: TipoDispositivo.objects.get_or_create(nome=nome, defaults=campos)[0]
        for nome in ("Articulação", "Artigo", "Caput")
    }
    vigencia = datetime.date(2020, 1, 1)

    def criar(tipo, ordem, nivel, pai=None, **kwargs):
        return Dispositivo.objects.create(
            ta=ta,
            tipo_dispositivo=tipos[tipo],
            ordem=ordem,
            nivel=nivel,
            dispositivo_pai=pai,
            inicio_vigencia=vigencia,
            inicio_eficacia=vigencia,
            **kwargs,
        )

    raiz = criar("Articulação", 1000, 0)
    art1 = criar("Artigo", 2000, 1, raiz, rotulo="Art. 1º.", dispositivo0=1)
    criar("Caput", 3000, 2, art1, texto="Primeiro texto do artigo.")
    art2 = criar("Artigo", 4000, 1, raiz, rotulo="Art. 2º.", dispositivo0=2)
    caput2 = criar("Caput", 5000, 2, art2, texto="Segundo texto do artigo.")
    return ta, art1, art2, caput2


def test_generate_chunks_v2_sincroniza_por_hash_e_nao_toca_no_v1():
    ta, art1, art2, caput2 = _norma_com_dois_artigos()
    ct = ContentType.objects.get_for_model(Dispositivo)
    v1 = Embedding.objects.create(content_type=ct, object_id=art1.pk, chunk="chunk v1")

    def v2():
        return Embedding.objects.filter(Embedding.strategy_filter("v2"))

    def por_objeto():
        return {e.object_id: e.pk for e in v2()}

    ta.generate_chunks_v2()
    assert v2().count() == 2
    assert all(e.search_vector for e in v2()) and all(e.total_tokens > 0 for e in v2())
    ids_antes = por_objeto()

    # sem mudança: nada é recriado (os vetores seriam mantidos)
    ta.generate_chunks_v2()
    assert por_objeto() == ids_antes

    # editar o Art. 2º recria só o chunk dele (sem efeito cascata no Art. 1º)
    caput2.texto = "Texto alterado do segundo artigo."
    caput2.save()
    ta.generate_chunks_v2()
    depois = por_objeto()
    assert depois[art1.pk] == ids_antes[art1.pk]
    assert depois[art2.pk] != ids_antes[art2.pk]
    assert len(depois) == 2

    # o v1 continua intacto, e a reindexação v1 não apaga o v2
    assert Embedding.objects.filter(pk=v1.pk).exists()
    ta.generate_chunks()
    assert v2().count() == 2


def test_task_so_chama_a_api_quando_vectorize(monkeypatch):
    from unittest import mock

    from cmj.search import tasks

    ta, *_ = _norma_com_dois_artigos()

    with mock.patch.object(
        tasks.Embedding, "generate_embeddings_for_queryset"
    ) as vetorizar:
        tasks.task_sync_embeddings_textoarticulado_function(
            [ta.pk], strategy="v2", vectorize=False
        )
        vetorizar.assert_not_called()
        assert Embedding.objects.filter(Embedding.strategy_filter("v2")).count() == 2

        tasks.task_sync_embeddings_textoarticulado_function(
            [ta.pk], strategy="v2", vectorize=True
        )
        vetorizar.assert_called_once()
