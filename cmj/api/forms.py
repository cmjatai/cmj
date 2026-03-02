from cmj.loa.models import PrestacaoContaRegistro
from drfautoapi.drfautoapi import ApiFilterSetMixin

class PrestacaoContaRegistroFilterSet(ApiFilterSetMixin):
    class Meta(ApiFilterSetMixin.Meta):
        model = PrestacaoContaRegistro

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)