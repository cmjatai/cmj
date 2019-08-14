from celery_haystack.indexes import CelerySearchIndex
from haystack.constants import Indexable

from cmj.sigad.models import Documento
from sapl.base.search_indexes import TextExtractField


class SigadTextExtractField(TextExtractField):
    pass


class DocumentoIndex(CelerySearchIndex, Indexable):
    model = Documento
    text = SigadTextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('titulo', 'string_extractor'),
            ('descricao', 'string_extractor'),
            ('texto', 'string_extractor'),
        )
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text.search_index = self

    def get_model(self):
        return self.model

    def index_queryset(self, using=None):
        return self.get_model().objects.public_all_docs()

    def get_updated_field(self):
        return 'data_ultima_atualizacao'
