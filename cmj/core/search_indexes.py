from celery_haystack.indexes import CelerySearchIndex
from haystack.constants import Indexable
from haystack.fields import DateTimeField

from sapl.base.search_indexes import TextExtractField as SaplTextExtractField
from sapl.sessao.models import SessaoPlenaria


class TextExtractField(SaplTextExtractField):

    def extract_data(self, obj):

        data = ''

        for attr, func in self.model_attr:
            if not hasattr(obj, attr) or not hasattr(self, func):
                raise Exception

            value = getattr(obj, attr)
            if not value:
                continue

            if callable(value):
                data += getattr(self, func)(value()) + '  '
            else:
                data += getattr(self, func)(value) + '  '

        data = data.replace('\n', ' ')

        return data


class SessaoPlenariaIndex(CelerySearchIndex, Indexable):
    model = SessaoPlenaria
    data = DateTimeField(model_attr='data_inicio', null=True)
    text = TextExtractField(
        document=True, use_template=True,
        model_attr=(
            ('__str__', 'string_extractor'),
            ('upload_pauta', 'file_extractor'),
            ('upload_ata', 'file_extractor'),
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
        return 'data_inicio'
