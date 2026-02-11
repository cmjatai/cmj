from collections import OrderedDict
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT
from django.db.models.fields.json import JSONField
from django.utils.datastructures import OrderedSet
from django.utils.translation import gettext_lazy as _
from pgvector.django.vector import VectorField
from pgvector.django.halfvec import HalfVectorField
from pgvector.django import CosineDistance, HnswIndex


from cmj.genia import IAGenaiBase
from cmj.mixins import CmjModelMixin
from cmj.utils import get_settings_auth_user_model


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
        vetor1536: Vetor de embedding com 1536 dimensões (compatível com
               text-embedding-3-large da OpenAI ou modelos similares).

    Example:
        >>> embed = Embedding.objects.create(chunk="Texto de exemplo")
        >>> embed.generate_embedding()  # Gera vetor via API de IA
        >>> embed.update_total_tokens()  # Atualiza contagem de tokens
    """

    # --- Campos de Metadados e Relacionamento Genérico ---
    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)

    # GenericForeignKey: permite vincular embedding a qualquer modelo Django
    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None,
        on_delete=PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    # --- Campos de Conteúdo e Tokenização ---
    chunk = models.TextField(
        verbose_name=_('Chunk de texto'),
        default='',
        blank=True, null=False,)

    total_tokens = models.PositiveIntegerField(
        verbose_name=_('Número de tokens'),
        default=0,
        blank=True, null=False,)

    # --- Campo Vetorial (pgvector) ---
    # 3072 dimensões: compatível com text-embedding-3-large (OpenAI)
    # ou modelos de embedding com dimensionalidade similar
    vetor = VectorField(
        dimensions=3072,
        default=None,
        null=True,
        blank=True,
        verbose_name=_('Vetor de embedding')
    )

    vetor1536 = HalfVectorField(
        dimensions=1536,
        default=None,
        null=True,
        blank=True,
        verbose_name=_('Vetor de embedding 1536')
    )

    class Meta:
        verbose_name = _('Embedding')
        verbose_name_plural = _('Embeddings')
        ordering = ('-id', )

        indexes = [
            # Índice composto para otimizar buscas por objeto relacionado
            models.Index(fields=['content_type', 'object_id']),
            # Índice HNSW para busca por similaridade em vetor1536
            HnswIndex(
                name='embedding_vetor1536_hnsw',
                fields=['vetor1536'],
                m=16,
                ef_construction=64,
                opclasses=['halfvec_cosine_ops'],
            ),
        ]

    def __str__(self):
        return f'Embedding {self.id} - Object {self.content_object} '

    def update_total_tokens(self):
        """
        Atualiza a contagem de tokens do chunk de texto.

        Utiliza o tokenizador da classe IAGenaiBase para calcular
        o número de tokens. Útil para controle de custos de API
        e validação de limites de contexto.
        """
        IAGenaiBase_instance = IAGenaiBase()
        self.total_tokens = IAGenaiBase_instance.count_tokens_in_text(self.chunk)
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
        embedding_vector = IAGenaiBase_instance.embed_content(self.chunk)
        self.vetor1536 = embedding_vector
        self.save()

    @classmethod
    def make_context(cls, query_embedding, top_k=50):
        # Busca os top_k embeddings mais próximos usando distância do cosseno
        # CosineDistance retorna valores entre 0 (idêntico) e 2 (oposto)
        embeddings = Embedding.objects.annotate(
                distance=CosineDistance('vetor1536', query_embedding)
            ).order_by('distance')[:top_k]

        embeddings = list(embeddings)

        tas = OrderedSet()
        for embed in embeddings:
            if embed.content_object and hasattr(embed.content_object, 'ta_id'):
                tas.add(embed.content_object.ta_id)

        ta_dict = {}
        for embed in embeddings:
            ta_id = getattr(embed.content_object, 'ta_id', None)
            if ta_id and ta_id in tas:
                if ta_id not in ta_dict:
                    ta_dict[ta_id] = []
                ta_dict[ta_id].append(embed)

        context = []
        for ta_id in tas:
            ta_dict[ta_id].sort(key=lambda e: e.content_object.ordem)
            for embed in ta_dict[ta_id]:
                context.append((embed.content_object, list(map(str.strip, embed.chunk.split('\n')))))

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

        return '\n'.join(context_list_of_str)

    @classmethod
    def make_context__old(cls, query_embedding, top_k=50):
        """
        Constrói contexto textual a partir dos embeddings mais similares.

        Falha: essa implementação falha ao lidar com dispositivos que possuem o mesmo texto mas com pais diferentes, causando perda de contexto relevante. A ordenação por similaridade é perdida ao usar o texto como chave, e o resultado final pode incluir apenas um dos dispositivos relevantes, mesmo que outros tenham o mesmo texto e sejam igualmente importantes para a resposta da IA.

        Implementa a etapa de "Retrieval" do padrão RAG, buscando os
        chunks mais semanticamente similares à query e formatando-os
        para uso como contexto em prompts de LLM.

        Args:
            query_embedding: Vetor de embedding da consulta do usuário
                            (deve ter 1536 dimensões).
            top_k: Número máximo de embeddings similares a recuperar.
                   Default: 50.

        Returns:
            str: Contexto formatado em texto, com chunks agrupados por
                 documento fonte e links para os textos articulados
                 originais no formato HTML.

        Note:
            O método assume que os content_objects possuem os atributos
            `ta_id` (ID do Texto Articulado) e `ordem` (ordem do dispositivo),
            típicos de modelos Dispositivo do módulo compilacao.
        """
        # Busca os top_k embeddings mais próximos usando distância do cosseno
        # CosineDistance retorna valores entre 0 (idêntico) e 2 (oposto)
        embeddings = Embedding.objects.annotate(
                distance=CosineDistance('vetor1536', query_embedding)
            ).order_by('distance')[:top_k]

        # Extrai chunks e objetos relacionados
        context = []
        for embed in embeddings:
            # Cada item é uma tupla: (objeto_fonte, lista_de_linhas_do_chunk)

            #similarity_score = 1 - embed.distance
            #print(f"Item ID: {embed.id}, Similarity: {similarity_score:.4f}, Tokens: {embed.total_tokens}")
            ##print(embed.content_object)
            #print(embed.chunk)
            #print('---'*10)

            context.append((embed.content_object, list(map(str.strip, embed.chunk.split('\n')))))

        # Preserva a ordem original de aparição das chaves (primeira linha de cada chunk)
        # para manter relevância semântica no resultado final
        keys = OrderedSet()
        for item in context:
            keys.add(item[1][0])

        # Ordena por documento (ta_id) e posição no documento (ordem)
        # para agrupar chunks do mesmo texto articulado
        context.sort(key=lambda x: (x[0].ta_id, x[0].ordem))

        # Agrupa chunks por documento fonte, removendo duplicatas
        # context_dict1: mapeia chave -> lista de linhas agregadas
        # context_dict2: mapeia chave -> objeto fonte (para gerar links)
        context_dict1 = OrderedDict()
        context_dict2 = {}
        for idx, (content_object, item) in enumerate(context):
            if item[0] not in context_dict1:
                context_dict1[item[0]] = [item[0]]
                context_dict2[item[0]] = content_object
            context_dict1[item[0]].extend(item[1:])

        # Reordena pelo ranking original de similaridade
        context_dict = OrderedDict()
        for key in keys:
            context_dict[key] = context_dict1[key]

        # Remove linhas duplicadas dentro de cada chunk agregado
        context = list(context_dict.values())
        for idx, item in enumerate(context):
            context[idx] = list(OrderedSet(item))

        # Formata saída final com links HTML para os textos articulados
        context_final = []
        for item in context:
            d = context_dict2[item[0]]
            # Adiciona link para o texto articulado fonte
            item[0] = f'\nFonte: <a href="/ta/{d.ta_id}/text">{item[0]}</a>'
            context_final.extend(item)

        context_final = '\n'.join(context_final)

        return context_final

class ChatSession(models.Model):
    user = models.ForeignKey(get_settings_auth_user_model(), on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    title = models.CharField(max_length=255, default="Nova Conversa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]
        permissions = [
            (
                'can_use_chat_module',
                'Usuário pode usar o módulo de chat'
            ),
        ]

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('model', 'Model'),
    ]

    chat = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['chat', 'timestamp']),
        ]

