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

from pgvector.django import CosineDistance


from cmj.genia import IAGenaiBase
from cmj.mixins import CmjModelMixin
from cmj.utils import get_settings_auth_user_model

class Embedding(CmjModelMixin):
    metadata = JSONField(
        verbose_name=_('Metadados'),
        blank=True, null=True, default=dict, encoder=DjangoJSONEncoder)
    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None,
        on_delete=PROTECT)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    chunk = models.TextField(
        verbose_name=_('Chunk de texto'),
        default='',
        blank=True, null=False,)

    total_tokens = models.PositiveIntegerField(
        verbose_name=_('Número de tokens'),
        default=0,
        blank=True, null=False,)

    vetor = VectorField(
        dimensions=3072,
        default=None,
        null=True,
        blank=True,
        verbose_name=_('Vetor de embedding')
    )

    class Meta:
        verbose_name = _('Embedding')
        verbose_name_plural = _('Embeddings')
        ordering = ('-id', )

        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'Embedding {self.id} - Object {self.content_object} '

    def update_total_tokens(self):
        IAGenaiBase_instance = IAGenaiBase()
        self.total_tokens = IAGenaiBase_instance.count_tokens_in_text(self.chunk)
        self.save()

    def generate_embedding(self):
        IAGenaiBase_instance = IAGenaiBase()
        embedding_vector = IAGenaiBase_instance.embed_content(self.chunk)
        self.vetor = embedding_vector
        self.save()

    @classmethod
    def make_context(cls, query_embedding, top_k=50):
        embeddings = Embedding.objects.annotate(
                distance=CosineDistance('vetor', query_embedding)
            ).order_by('distance')[:top_k]

        context = []
        for embed in embeddings:
            #similarity_score = 1 - embed.distance
            #print(f"Item ID: {embed.id}, Similarity: {similarity_score:.4f}, Tokens: {embed.total_tokens}")
            ##print(embed.content_object)
            #print(embed.chunk)
            #print('---'*10)
            context.append((embed.content_object, list(map(str.strip, embed.chunk.split('\n')))))

        keys = OrderedSet()
        for item in context:
            keys.add(item[1][0])

        context.sort(key=lambda x: (x[0].ta_id, x[0].ordem))

        context_dict1 = OrderedDict()
        context_dict2 = {}
        for idx, (content_object, item) in enumerate(context):
            if item[0] not in context_dict1:
                context_dict1[item[0]] = [item[0]]
                context_dict2[item[0]] = content_object
            context_dict1[item[0]].extend(item[1:])


        context_dict = OrderedDict()
        for key in keys:
            context_dict[key] = context_dict1[key]

        context = list(context_dict.values())
        for idx, item in enumerate(context):
            context[idx] = list(OrderedSet(item))

        context_final = []
        for item in context:
            d = context_dict2[item[0]]
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

