from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT
from django.db.models.fields.json import JSONField
from django.utils.translation import gettext_lazy as _
from pgvector.django.vector import VectorField

from cmj.genia import IAGenaiBase
from cmj.mixins import CmjModelMixin

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