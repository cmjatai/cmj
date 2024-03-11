from celery_haystack.indexes import CelerySearchIndex
from haystack.constants import Indexable
from haystack.fields import DateTimeField, IntegerField

from sapl.base.search_indexes import TextExtractField
from sapl.sessao.models import SessaoPlenaria


class SessaoPlenariaIndex(CelerySearchIndex, Indexable):
    model = SessaoPlenaria
    data = DateTimeField(model_attr='data_inicio', null=True)
    ano = IntegerField(model_attr='ano')

    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('__str__', 'string_extractor'),
            ('upload_ata', 'file_extractor'),
            ('upload_pauta', 'file_extractor'),
            ('upload_anexo', 'file_extractor'),


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
