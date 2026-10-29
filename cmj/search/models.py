import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT
from django.db.models.fields.json import JSONField
from django.utils.datastructures import OrderedSet
from django.utils.translation import gettext_lazy as _
from pgvector.django import CosineDistance, HnswIndex
from pgvector.django.halfvec import HalfVectorField
from pgvector.django.vector import VectorField

from cmj.mixins import CmjModelMixin
from cmj.search.fts import build_fts_queries
from cmj.utils import get_settings_auth_user_model
from cmj.utils.genia import IAGenaiBase

logger = logging.getLogger(__name__)


class Embedding(CmjModelMixin):
    """
    Modelo para armazenamento de embeddings vetoriais de texto.

    Utiliza pgvector para busca por similaridade semântica, permitindo
    implementar funcionalidades de RAG (Retrieval-Augmented Generation)
    no sistema CMJ.

    O modelo usa GenericForeignKey para associar embeddings a qualquer
    objeto do sistema (ex: Dispositivos de Texto Articulado, Normas, etc.),
    permitindo indexação semântica flexível de conteúdo legislativo.

    Attributes:
        metadata: Dados adicionais em JSON para extensibilidade.
        content_type: Tipo do modelo Django associado (via ContentType).
        object_id: ID do objeto associado.
        content_object: Referência genérica ao objeto fonte do embedding.
        chunk: Fragmento de texto que foi vetorizado.
        total_tokens: Contagem de tokens do chunk (útil para controle de custos).
        vetor1536: Vetor de embedding com 1536 dimensões gerado pelo
               gemini-embedding-2 (usado na busca semântica).

    Example:
        >>> embed = Embedding.objects.create(chunk="Texto de exemplo")
        >>> embed.generate_embedding()  # Gera vetor via API de IA
        >>> embed.update_total_tokens()  # Atualiza contagem de tokens
    """

    # --- Campos de Metadados e Relacionamento Genérico ---
    metadata = JSONField(
        verbose_name=_("Metadados"),
        blank=True,
        null=True,
        default=dict,
        encoder=DjangoJSONEncoder,
    )

    # GenericForeignKey: permite vincular embedding a qualquer modelo Django
    content_type = models.ForeignKey(
        ContentType, blank=True, null=True, default=None, on_delete=PROTECT
    )
    object_id = models.PositiveIntegerField(blank=True, null=True, default=None)
    content_object = GenericForeignKey("content_type", "object_id")

    # --- Campos de Conteúdo e Tokenização ---
    chunk = models.TextField(
        verbose_name=_("Chunk de texto"),
        default="",
        blank=True,
        null=False,
    )

    total_tokens = models.PositiveIntegerField(
        verbose_name=_("Número de tokens"),
        default=0,
        blank=True,
        null=False,
    )

    # --- Campo Vetorial (pgvector) ---
    # Legado (3072 dimensões, modelo anterior): não é mais lido nem preenchido;
    # use vetor1536.
    vetor = VectorField(
        dimensions=3072,
        default=None,
        null=True,
        blank=True,
        verbose_name=_("Vetor de embedding"),
    )

    vetor1536 = HalfVectorField(
        dimensions=1536,
        default=None,
        null=True,
        blank=True,
        verbose_name=_("Vetor de embedding 1536"),
    )

    search_vector = SearchVectorField(
        null=True, blank=True, default=None, verbose_name=_("Vetor de busca full-text")
    )

    class Meta:
        verbose_name = _("Embedding")
        verbose_name_plural = _("Embeddings")
        ordering = ("-id",)

        indexes = [
            # Índice composto para otimizar buscas por objeto relacionado
            models.Index(fields=["content_type", "object_id"]),
            # Índice HNSW para busca por similaridade em vetor1536
            HnswIndex(
                name="embedding_vetor1536_hnsw",
                fields=["vetor1536"],
                m=16,
                ef_construction=64,
                opclasses=["halfvec_cosine_ops"],
            ),
            # Índice GIN para busca de texto completo no campo chunk
            GinIndex(
                name="embedding_search_vector_gin",
                fields=["search_vector"],
            ),
        ]

    def __str__(self):
        return f'Embedding {self.id} - Object {self.content_object} - T.A. {getattr(self.content_object, "ta_id", "N/A")} - Tokens: {self.total_tokens}'

    def update_total_tokens(self):
        """
        Atualiza a contagem de tokens do chunk de texto.

        Utiliza o tokenizador da classe IAGenaiBase para calcular
        o número de tokens. Útil para controle de custos de API
        e validação de limites de contexto.
        """
        IAGenaiBase_instance = IAGenaiBase()
        self.total_tokens = IAGenaiBase_instance.count_tokens_in_text(self.chunk) or 0
        self.save()

    def generate_embedding(self):
        """
        Gera o vetor de embedding a partir do chunk de texto.

        Utiliza a API de embedding configurada em IAGenaiBase
        para converter o texto em representação vetorial de 1536 dimensões.
        O vetor resultante é salvo no campo `vetor1536` para uso em
        buscas por similaridade semântica.
        """
        IAGenaiBase_instance = IAGenaiBase()
        embedding_vector = IAGenaiBase_instance.embed_documents(
            [{"text": self.chunk, "title": None}]
        )
        self.vetor1536 = embedding_vector[0] if embedding_vector else None
        self.save()

    @classmethod
    def generate_embeddings_for_queryset(cls, queryset, slice_size=256):
        """
        Vetoriza os embeddings do queryset em fatias, gravando o progresso a
        cada fatia. Embeddings cuja vetorização falhar continuam sem vetor
        (pendentes) e serão retomados numa próxima execução.

        Returns:
            int: quantidade de embeddings vetorizados.
        """
        ids = sorted(set(queryset.order_by().values_list("id", flat=True)))
        if not ids:
            return 0

        ia = IAGenaiBase()
        done = 0
        for start in range(0, len(ids), slice_size):
            slice_ids = ids[start : start + slice_size]
            embs = list(
                cls.objects.filter(id__in=slice_ids).only("id", "chunk").order_by("id")
            )
            vectors = ia.embed_documents(
                [{"text": e.chunk, "title": None} for e in embs]
            )

            for emb, vector in zip(embs, vectors):
                if vector:
                    cls.objects.filter(pk=emb.pk).update(vetor1536=vector, vetor=None)
                    done += 1

            if len(vectors) < len(embs):
                logger.warning(
                    "Vetorização interrompida: API indisponível. Pendentes serão retomados."
                )
                break
        return done

    def update_search_vector(self):
        """
        Popula o campo search_vector a partir do conteúdo do chunk.

        Utiliza a configuração 'portuguese' do PostgreSQL para gerar
        o tsvector adequado para busca full-text em português.
        """
        from django.contrib.postgres.search import SearchVector

        Embedding.objects.filter(pk=self.pk).update(
            search_vector=SearchVector("chunk", config="portuguese")
        )
        self.refresh_from_db(fields=["search_vector"])

    @classmethod
    def update_all_search_vectors(cls):
        """
        Popula o search_vector de todos os Embeddings em batch.

        Mais eficiente que chamar update_search_vector() individualmente,
        pois executa um único UPDATE no banco.
        """
        from django.contrib.postgres.search import SearchVector

        cls.objects.update(search_vector=SearchVector("chunk", config="portuguese"))

    @classmethod
    def _fts_ids(cls, search_query, top_k):
        """
        IDs dos embeddings por Full-Text Search, em duas camadas: primeiro os
        que contêm TODOS os termos (AND); se houver menos que top_k, completa
        com os que contêm QUALQUER termo (OR), sempre abaixo dos primeiros.
        """
        from django.contrib.postgres.search import SearchRank

        query_and, query_or = build_fts_queries(search_query)
        if query_and is None:
            return []

        def ranked_ids(fts_query, limit, exclude=()):
            return list(
                cls.objects.filter(search_vector=fts_query)
                .exclude(id__in=exclude)
                .annotate(fts_rank=SearchRank("search_vector", fts_query))
                .order_by("-fts_rank")[:limit]
                .values_list("id", flat=True)
            )

        ids = ranked_ids(query_and, top_k)
        if len(ids) < top_k and query_or is not None:
            ids += ranked_ids(query_or, top_k - len(ids), exclude=ids)
        return ids

    @classmethod
    def make_context(cls, search_query, query_embedding, top_k=60):
        RRF_K = 60  # Constante de suavização para Reciprocal Rank Fusion

        # 1. Busca semântica via pgvector (distância do cosseno)
        semantic_ids = list(
            Embedding.objects.filter(vetor1536__isnull=False)
            .annotate(distance=CosineDistance("vetor1536", query_embedding))
            .order_by("distance")[:top_k]
            .values_list("id", flat=True)
        )

        # 2. Busca por palavra-chave via Full-Text Search (PostgreSQL)
        text_ids = cls._fts_ids(search_query, top_k)

        # 3. Reciprocal Rank Fusion (RRF)
        # score = 1/(k + rank_semantico) + 1/(k + rank_texto)
        rrf_scores = {}
        for rank, eid in enumerate(semantic_ids, start=1):
            rrf_scores[eid] = rrf_scores.get(eid, 0) + 1.0 / (RRF_K + rank)

        for rank, eid in enumerate(text_ids, start=1):
            rrf_scores[eid] = rrf_scores.get(eid, 0) + 1.0 / (RRF_K + rank)

        # 4. Ordena por score RRF decrescente e seleciona top_k
        sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]

        # 5. Busca os embeddings completos preservando a ordem RRF
        embeddings_map = Embedding.objects.in_bulk(sorted_ids)
        embeddings = [
            embeddings_map[eid] for eid in sorted_ids if eid in embeddings_map
        ]

        tas = OrderedSet()
        for embed in embeddings:
            if embed.content_object and hasattr(embed.content_object, "ta_id"):
                tas.add(embed.content_object.ta_id)

        ta_dict = {}
        for embed in embeddings:
            ta_id = getattr(embed.content_object, "ta_id", None)
            if ta_id and ta_id in tas:
                if ta_id not in ta_dict:
                    ta_dict[ta_id] = []
                ta_dict[ta_id].append(embed)

        context = []
        for ta_id in tas:
            ta_dict[ta_id].sort(key=lambda e: e.content_object.ordem)
            for embed in ta_dict[ta_id]:
                context.append(
                    (
                        embed.content_object,
                        list(map(str.strip, embed.chunk.split("\n"))),
                    )
                )

        context_list_of_list = []
        for item in context:
            d = item[0]
            d_item = item[1]
            d_item[0] = f'\nFonte: <a href="/ta/{d.ta_id}/text">{d_item[0]}</a>'
            context_list_of_list.append(d_item)

        context_list_of_str = []
        while True:
            item_str = None
            for list_of_str in context_list_of_list:
                if not list_of_str:
                    continue
                if item_str is None:
                    item_str = list_of_str.pop(0)
                    continue
                if item_str == list_of_str[0]:
                    list_of_str.pop(0)
                    continue
                break
            if item_str is None:
                break
            context_list_of_str.append(item_str)

        return "\n".join(context_list_of_str)


class ChatSession(models.Model):
    user = models.ForeignKey(get_settings_auth_user_model(), on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    title = models.CharField(max_length=255, default="Nova Conversa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-updated_at"]),
        ]
        permissions = [
            ("can_use_chat_module", "Usuário pode usar o módulo de chat"),
        ]


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("model", "Model"),
    ]

    chat = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["chat", "timestamp"]),
        ]
