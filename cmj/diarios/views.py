from builtins import property

from cmj.diarios.models import TipoDeDiario, DiarioOficial
from sapl.crud.base import CrudAux, Crud, RP_DETAIL, RP_LIST


TipoDeDiarioCrud = CrudAux.build(TipoDeDiario, None)


class DiarioOficialCrud(Crud):
    model = DiarioOficial
    help_topic = 'diariooficial'
    public = [RP_LIST, RP_DETAIL]
