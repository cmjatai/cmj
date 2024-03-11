from celery_haystack.indexes import CelerySearchIndex
from haystack.constants import Indexable
from haystack.fields import CharField, DateTimeField, IntegerField
from cmj.arq.models import ArqDoc
from sapl.base.search_indexes import TextExtractField


class ArqTextExtractField(TextExtractField):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ArqDocIndex(CelerySearchIndex, Indexable):
    model = ArqDoc
    data = DateTimeField(model_attr='data')

    text = ArqTextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('titulo', 'string_extractor'),
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
        return 'modified'
