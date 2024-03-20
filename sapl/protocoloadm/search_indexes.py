from celery_haystack.indexes import CelerySearchIndex
from haystack.constants import Indexable
from haystack.fields import DateTimeField, IntegerField

from sapl.base.search_indexes import TextExtractField
from sapl.protocoloadm.models import DocumentoAdministrativo


class DocumentoAdministrativoIndex(CelerySearchIndex, Indexable):
    model = DocumentoAdministrativo
    data = DateTimeField(model_attr='data', null=True)
    ano = IntegerField(model_attr='ano', null=True)
    at = IntegerField(model_attr='workspace_id', null=True)
    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('__str__', 'string_extractor'),
            ('texto_integral', 'file_extractor'),
            ('assunto', 'string_extractor'),
            ('observacao', 'string_extractor'),
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
