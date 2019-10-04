from builtins import property

from cmj.diarios.models import TipoDeDiario, DiarioOficial
from sapl.crud.base import CrudAux, Crud, RP_DETAIL, RP_LIST


TipoDeDiarioCrud = CrudAux.build(TipoDeDiario, None)


class DiarioOficialCrud(Crud):
    model = DiarioOficial
    help_topic = 'diariooficial'
    public = [RP_LIST, RP_DETAIL]

    class ListView(Crud.ListView):
        def get_context_data(self, **kwargs):
            c = super().get_context_data(**kwargs)
            c['bg_title'] = 'bg-maroon text-white'
            return c

    class DetailView(Crud.DetailView):
        def get_context_data(self, **kwargs):
            c = super().get_context_data(**kwargs)
            c['bg_title'] = 'bg-maroon text-white'
            return c
