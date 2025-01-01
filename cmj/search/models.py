
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT
from django.db.models.fields.json import JSONField
from django.utils.translation import gettext_lazy as _
from pgvector.django.vector import VectorField

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

    embedding = VectorField()

    class Meta:
        verbose_name = _('Embedding')
        verbose_name_plural = _('Embeddings')
        ordering = ('-id', )
