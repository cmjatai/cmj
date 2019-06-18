from cmj.crud.base import CrudAux
from cmj.diarios.models import TipoDeDiario


TipoDeDiarioCrud = CrudAux.build(TipoDeDiario, None)
