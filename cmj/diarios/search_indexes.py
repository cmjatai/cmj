from celery_haystack.indexes import CelerySearchIndex
from haystack.constants import Indexable
from haystack.fields import DateTimeField

from cmj.diarios.models import DiarioOficial
from sapl.base.search_indexes import TextExtractField


class DiarioOficialIndex(CelerySearchIndex, Indexable):
    model = DiarioOficial
    data = DateTimeField(model_attr='data', null=True)
    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('descricao', 'string_extractor'),
            ('arquivo', 'file_extractor'),
        )
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text.search_index = self

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_updated_field(self):
        return 'data_ultima_atualizacao'
